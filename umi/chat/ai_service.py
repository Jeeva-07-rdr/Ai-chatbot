import os
import json
import time
import logging
import requests
from django.conf import settings
from django.core.cache import cache
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger('umi')

OLLAMA_HOST = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Persistent HTTP Session for connection pooling
http_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
http_session.mount('http://', adapter)
http_session.mount('https://', adapter)

# Client caching dictionary for Gemini
_gemini_clients = {}

def get_gemini_client(api_key):
    """
    Returns a cached Gemini client for the API key to avoid rebuilding it.
    """
    if api_key not in _gemini_clients:
        _gemini_clients[api_key] = genai.Client(api_key=api_key)
    return _gemini_clients[api_key]

class AIServiceError(Exception):
    pass


def get_ollama_models():
    """
    Queries local Ollama list endpoint and returns available model tags.
    Caches model list for 1 hour to prevent blocking.
    """
    cache_key = 'ollama_models_list'
    cached_models = cache.get(cache_key)
    if cached_models is not None:
        return cached_models

    url = f"{OLLAMA_HOST}/api/tags"
    try:
        res = http_session.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            models = [m['name'] for m in data.get('models', [])]
            logger.debug(f"OLLAMA | Models fetched: {models}")
            cache.set(cache_key, models, 3600)  # Cache for 1 hour
            return models
    except requests.exceptions.ConnectionError:
        logger.warning("OLLAMA | Server not reachable at {}".format(OLLAMA_HOST))
    except Exception as e:
        logger.error(f"OLLAMA | Error fetching models: {e}")
    return []


def get_system_prompt_for_style(style):
    """
    Returns an optimized system prompt customized for the selected response style.
    Instructs the model on output formatting, detailed explanations, lists, tables,
    and coding/educational step-by-step styles.
    """
    base_instructions = (
        "You are UMI, a premium, highly intelligent, professional, and helpful AI assistant. "
        "Your communication style is clear, expert-grade, polite, and authoritative. "
        "You always identify yourself as UMI.\n\n"
        
        "Formatting Guidelines:\n"
        "- Use markdown headings (# Main Heading, ## Subheading) to organize sections.\n"
        "- Use bullet points for lists and numbered lists for steps or processes.\n"
        "- Use tables when organizing structured data comparisons.\n"
        "- Use bold text for key terms and concepts.\n"
        "- Include practical examples and real-world applications whenever explaining concepts.\n\n"
        
        "Educational Explanations:\n"
        "- Explain concepts starting from a clear beginner level, then build up to advanced concepts step by step. Do not assume prior knowledge.\n\n"
        
        "Programming & Technical Requests:\n"
        "- If code is discussed, always include: a clear explanation, standard syntax, a practical example, a line-by-line explanation of the code, common mistakes, best practices, alternative approaches, and a real-world use case.\n"
        "- Enclose all code blocks in proper fenced markdown syntax with language tags.\n\n"
        
        "Behavioral Constraints:\n"
        "- Avoid conversational filler, repetitive prefixes, or self-referential disclaimers (e.g. do NOT say 'As an AI...').\n"
        "- Never give extremely short one-line replies unless the user explicitly asks for a summary, brief response, or yes/no answer."
    )
    
    if style == 'short':
        return (
            base_instructions +
            "\nStyle Constraint (Short): Keep responses highly concise and straight-to-the-point, while maintaining UMI's professional formatting."
        )
    elif style == 'detailed':
        return (
            base_instructions +
            "\nStyle Constraint (Detailed): Provide extremely thorough explanations, explore background context in detail, and discuss multiple perspectives, pros/cons, and comprehensive scenarios."
        )
    elif style == 'research':
        return (
            base_instructions +
            "\nStyle Constraint (Research): Provide exhaustive, academic-grade analysis. Cover extensive history, theoretical foundations, detailed step-by-step methodologies, pros and cons, multiple alternative approaches, and deep technical details."
        )
    else: # Balanced
        return (
            base_instructions +
            "\nStyle Constraint (Balanced): Deliver well-structured, informative, and naturally structured answers that are comprehensive yet easy to read."
        )


def stream_ai_response(provider, model, prompt, history, system_prompt=None, multimodal_parts=None, response_style='balanced'):
    """
    Generator function that yields chunks of text generated by the selected AI model.
    """
    limits = {
        'short': 250,
        'balanced': 1500,
        'detailed': 3000,
        'research': 4000
    }
    max_tokens = limits.get(response_style, 1500)

    if provider == 'gemini':
        # Load fresh variables on request to avoid caching issues with running Django dev server instances
        load_dotenv(override=True)
        api_key = os.environ.get("GEMINI_API_KEY", "")
        
        if not api_key or api_key == 'YOUR_API_KEY':
            logger.error("GEMINI | API key not configured or is placeholder")
            yield "Error: Gemini API Key is not configured. Please verify your GEMINI_API_KEY in the .env file."
            return
            
        # Map history to Gemini contents format using the official SDK types
        contents = []
        for msg in history:
            role = "user" if msg['role'] == 'user' else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg['content'])]
                )
            )
            
        # Compile parts for user prompt (text + multimodal files)
        user_parts = [types.Part.from_text(text=prompt)]
        if multimodal_parts:
            for part in multimodal_parts:
                try:
                    user_parts.append(
                        types.Part.from_bytes(
                            data=part['bytes'],
                            mime_type=part['mime_type']
                        )
                    )
                except Exception as e:
                    yield f"\n[Error parsing attachment data: {e}]\n"
                    
        # Add current user prompt
        contents.append(
            types.Content(
                role="user",
                parts=user_parts
            )
        )
        
        # Determine model: fallback to gemini-2.5-flash if none specified
        gemini_model = model if model else "gemini-2.5-flash"
        
        try:
            client = get_gemini_client(api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                max_output_tokens=max_tokens
            )
            logger.info(f"GEMINI | Request sent | Model: {gemini_model} | max_output_tokens: {max_tokens}")
            gen_start = time.time()
            response = client.models.generate_content_stream(
                model=gemini_model,
                contents=contents,
                config=config
            )
            char_count = 0
            for chunk in response:
                if chunk.text:
                    char_count += len(chunk.text)
                    yield chunk.text
            gen_duration = round(time.time() - gen_start, 2)
            logger.success(f"GEMINI | Response received | Model: {gemini_model} | Duration: {gen_duration}s | Characters: {char_count}")
        except APIError as e:
            if e.code == 403 or e.code == 401:
                logger.error(f"GEMINI | Invalid API key (HTTP {e.code})")
                yield "Error: Invalid Gemini API key. Please check your GEMINI_API_KEY in the .env file."
            elif e.code == 429:
                logger.warning(f"GEMINI | Rate limit exceeded (HTTP 429)")
                yield "Error: Gemini rate limit exceeded. Please wait a moment before trying again."
            else:
                logger.error(f"GEMINI | API error (HTTP {e.code}): {e.message}")
                yield f"Google Gemini API Error (HTTP {e.code}): {e.message}"
        except Exception as e:
            logger.error(f"GEMINI | Connection error: {e}")
            yield f"Error: Unable to connect to Gemini. Please check your internet connection. ({e})"
            
    else: # Ollama backend
        url = f"{OLLAMA_HOST}/api/chat"
        
        # Format messages for Ollama chat endpoint
        messages = []
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        for msg in history:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
            
        # Append latest prompt with UMI persona reminder
        prompt_with_reminder = (
            f"[System Instruction: You are UMI. You must refer to yourself as UMI. "
            f"Do not mention Qwen or Alibaba. Respond as UMI.]\n\n"
            f"User: {prompt}"
        )
        messages.append({
            'role': 'user',
            'content': prompt_with_reminder
        })
        
        ollama_model = model if model else 'qwen2.5:0.5b'
        payload = {
            'model': ollama_model,
            'messages': messages,
            'stream': True,
            'keep_alive': '5m',  # Keep model loaded in VRAM for 5 minutes of inactivity
            'options': {
                'num_ctx': 16384,  # Support up to 16k tokens for analyzing files
                'num_predict': max_tokens  # Maps to Ollama max output tokens
            }
        }
        
        logger.info(f"OLLAMA | Request sent | Model: {ollama_model} | Context: 16384 tokens | keep_alive: 5m | num_predict: {max_tokens}")
        gen_start = time.time()
        
        try:
            res = http_session.post(url, json=payload, stream=True, timeout=180)
            if res.status_code != 200:
                logger.error(f"OLLAMA | HTTP error {res.status_code}: {res.text[:200]}")
                yield f"Ollama returned error status (HTTP {res.status_code}): {res.text}"
                return
                
            char_count = 0
            for line in res.iter_lines():
                if line:
                    try:
                        chunk_json = json.loads(line.decode('utf-8'))
                        if 'message' in chunk_json and 'content' in chunk_json['message']:
                            chunk_content = chunk_json['message']['content']
                            # Post-processing replacement filter for UMI persona
                            chunk_content = chunk_content.replace("Qwen", "UMI")
                            chunk_content = chunk_content.replace("Alibaba Cloud", "UMI Team")
                            chunk_content = chunk_content.replace("Alibaba", "UMI Team")
                            char_count += len(chunk_content)
                            yield chunk_content
                    except Exception:
                        pass
            gen_duration = round(time.time() - gen_start, 2)
            logger.success(f"OLLAMA | Response received | Model: {ollama_model} | Duration: {gen_duration}s | Characters: {char_count}")
        except requests.exceptions.Timeout:
            logger.error(f"OLLAMA | Request timed out after 180s | Model: {ollama_model}")
            yield "Error: Request to Ollama timed out."
        except requests.exceptions.ConnectionError:
            logger.error(f"OLLAMA | Connection failed | Server: {OLLAMA_HOST}")
            yield "Ollama is not running. Please start Ollama using 'ollama serve'."
        except Exception as e:
            logger.error(f"OLLAMA | Unexpected error: {e}")
            yield f"Error communicating with Ollama: {e}"
