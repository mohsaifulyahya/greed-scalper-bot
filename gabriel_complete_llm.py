"""
GABRIEL - Complete LLM Setup File
Semua konfigurasi LLM dalam 1 file untuk copy-paste

Fitur:
✅ Anthropic Claude
✅ Groq
✅ Depsek
✅ Gemini
✅ FreeLLMAPI Support
✅ LLM Rotation (Priority: Anthropic → Groq → Depsek → Gemini)
✅ Vision (Baca gambar)
✅ Audio (Speech-to-Text / Text-to-Speech)
✅ Error Handling & Fallback
✅ Memory & Learning

Usage:
1. Copy file ini
2. Simpan sebagai: gabriel_complete_llm.py
3. Update .env dengan API keys
4. Import: from gabriel_complete_llm import GABRIELLLMComplete
5. Gunakan: llm = GABRIELLLMComplete()

Author: GABRIEL AI
Version: 1.0.0
License: MIT
"""

import os
import logging
import asyncio
import time
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dotenv import load_dotenv

# ============================================================================
# LOAD ENVIRONMENT
# ============================================================================

load_dotenv()

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GABRIEL LLM - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# API KEYS CONFIGURATION
# ============================================================================

# LLM API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "mixtral-8x7b-32768"

DEPSEK_API_KEY = os.getenv("DEPSEK_API_KEY")
DEPSEK_BASE_URL = os.getenv("DEPSEK_BASE_URL", "https://api.depsek.ai")
DEPSEK_MODEL = "depsek-pro"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-pro"

# Optional: FreeLLMAPI
FREELLMAPI_ENDPOINT = os.getenv("FREELLMAPI_ENDPOINT", "http://localhost:8000/v1")
FREELLMAPI_API_KEY = os.getenv("FREELLMAPI_API_KEY", "free")

# Audio/Vision APIs (Optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # For Whisper STT
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")  # For TTS

# ============================================================================
# LLM ROUTER CLASS
# ============================================================================

class GABRIELLLMComplete:
    """
    Complete LLM system dengan:
    - Multi-LLM routing (Anthropic → Groq → Depsek → Gemini)
    - Vision (baca gambar)
    - Audio (STT/TTS)
    - Memory & learning
    - Fallback & error handling
    """
    
    def __init__(self, use_freellmapi: bool = False):
        """
        Initialize GABRIEL LLM System
        
        Args:
            use_freellmapi: Use FreeLLMAPI instead of individual APIs
        """
        self.use_freellmapi = use_freellmapi
        self.priority_order = ["anthropic", "groq", "depsek", "gemini"]
        self.timeout = 30
        self.max_retries = 3
        
        self.clients = {}
        self.model_stats = {model: {"success": 0, "fail": 0, "avg_time": 0} 
                           for model in self.priority_order}
        self.memory = {"conversations": [], "trades": [], "patterns": []}
        
        self._initialize_clients()
        logger.info("✓ GABRIEL LLM System initialized")
    
    def _initialize_clients(self):
        """Initialize all LLM clients"""
        
        if self.use_freellmapi:
            logger.info("📡 Using FreeLLMAPI endpoint")
            self.clients["freellmapi"] = {
                "endpoint": FREELLMAPI_ENDPOINT,
                "api_key": FREELLMAPI_API_KEY
            }
            return
        
        # Anthropic Claude
        if ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.clients["anthropic"] = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                logger.info("✓ Anthropic Claude initialized")
            except Exception as e:
                logger.warning(f"✗ Anthropic failed: {e}")
        
        # Groq
        if GROQ_API_KEY:
            try:
                from groq import Groq
                self.clients["groq"] = Groq(api_key=GROQ_API_KEY)
                logger.info("✓ Groq initialized")
            except Exception as e:
                logger.warning(f"✗ Groq failed: {e}")
        
        # Depsek
        if DEPSEK_API_KEY:
            try:
                import requests
                self.clients["depsek"] = {
                    "base_url": DEPSEK_BASE_URL,
                    "api_key": DEPSEK_API_KEY,
                    "session": requests.Session()
                }
                logger.info("✓ Depsek initialized")
            except Exception as e:
                logger.warning(f"✗ Depsek failed: {e}")
        
        # Gemini
        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self.clients["gemini"] = genai.GenerativeModel(GEMINI_MODEL)
                logger.info("✓ Gemini initialized")
            except Exception as e:
                logger.warning(f"✗ Gemini failed: {e}")
    
    # ========================================================================
    # TEXT QUERIES
    # ========================================================================
    
    def query(self, prompt: str, context: Optional[Dict] = None, 
              max_tokens: int = 2000) -> str:
        """
        Query LLM dengan intelligent routing
        
        Args:
            prompt: User question/prompt
            context: Additional context (market data, trading info, etc)
            max_tokens: Max response tokens
        
        Returns:
            LLM response
        """
        full_prompt = self._build_prompt(prompt, context)
        
        # Try each LLM in priority order
        for llm_name in self.priority_order:
            try:
                start_time = time.time()
                response = self._query_llm_sync(llm_name, full_prompt, max_tokens)
                elapsed = time.time() - start_time
                
                self.model_stats[llm_name]["success"] += 1
                self.model_stats[llm_name]["avg_time"] = elapsed
                
                logger.info(f"✓ {llm_name} ({elapsed:.2f}s)")
                
                # Save to memory
                self._save_to_memory("conversation", {
                    "timestamp": datetime.now().isoformat(),
                    "model": llm_name,
                    "prompt": prompt,
                    "response": response[:100],  # First 100 chars
                    "tokens": len(response.split())
                })
                
                return response
                
            except Exception as e:
                logger.warning(f"✗ {llm_name}: {e}")
                self.model_stats[llm_name]["fail"] += 1
                
                if llm_name == self.priority_order[-1]:
                    # Last resort
                    return "⚠️ Unable to reach AI models. Please check API connections."
        
        return "❌ All LLM services unavailable"
    
    def _query_llm_sync(self, llm_name: str, prompt: str, max_tokens: int) -> str:
        """Query specific LLM (synchronous)"""
        
        if llm_name == "anthropic":
            return self._query_anthropic(prompt, max_tokens)
        elif llm_name == "groq":
            return self._query_groq(prompt, max_tokens)
        elif llm_name == "depsek":
            return self._query_depsek(prompt, max_tokens)
        elif llm_name == "gemini":
            return self._query_gemini(prompt, max_tokens)
        else:
            raise ValueError(f"Unknown LLM: {llm_name}")
    
    def _query_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Query Anthropic Claude"""
        response = self.clients["anthropic"].messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def _query_groq(self, prompt: str, max_tokens: int) -> str:
        """Query Groq"""
        response = self.clients["groq"].chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def _query_depsek(self, prompt: str, max_tokens: int) -> str:
        """Query Depsek"""
        headers = {
            "Authorization": f"Bearer {DEPSEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": DEPSEK_MODEL,
            "prompt": prompt,
            "max_tokens": max_tokens
        }
        response = self.clients["depsek"]["session"].post(
            f"{DEPSEK_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        result = response.json()
        return result.get("choices", [{}])[0].get("text", "No response")
    
    def _query_gemini(self, prompt: str, max_tokens: int) -> str:
        """Query Google Gemini"""
        response = self.clients["gemini"].generate_content(prompt)
        return response.text
    
    # ========================================================================
    # VISION - BACA GAMBAR
    # ========================================================================
    
    def analyze_image(self, image_path: str, prompt: str = None) -> str:
        """
        Analyze image/photo (Vision capability)
        
        Args:
            image_path: Path to image file
            prompt: Additional prompt for analysis
        
        Returns:
            Image analysis
        """
        if not prompt:
            prompt = "Analyze this image and describe what you see."
        
        try:
            # Try Claude Vision first (best quality)
            if "anthropic" in self.clients:
                return self._analyze_with_claude_vision(image_path, prompt)
            
            # Fallback to Gemini Vision
            elif "gemini" in self.clients:
                return self._analyze_with_gemini_vision(image_path, prompt)
            
            else:
                return "❌ Vision models not available"
        
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return f"⚠�� Could not analyze image: {e}"
    
    def _analyze_with_claude_vision(self, image_path: str, prompt: str) -> str:
        """Analyze image with Claude Vision"""
        import base64
        
        # Read image
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
        
        # Determine media type
        ext = image_path.lower().split('.')[-1]
        media_type_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "gif": "image/gif",
            "webp": "image/webp"
        }
        media_type = media_type_map.get(ext, "image/jpeg")
        
        # Query with vision
        response = self.clients["anthropic"].messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }]
        )
        
        return response.content[0].text
    
    def _analyze_with_gemini_vision(self, image_path: str, prompt: str) -> str:
        """Analyze image with Gemini Vision"""
        from PIL import Image
        
        image = Image.open(image_path)
        response = self.clients["gemini"].generate_content([prompt, image])
        return response.text
    
    # ========================================================================
    # AUDIO - SPEECH-TO-TEXT & TEXT-TO-SPEECH
    # ========================================================================
    
    def speech_to_text(self, audio_path: str) -> str:
        """
        Convert speech to text (Speech-to-Text)
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Transcribed text
        """
        try:
            if OPENAI_API_KEY:
                return self._speech_to_text_whisper(audio_path)
            else:
                return "⚠️ Whisper API key not configured"
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return f"❌ Speech-to-text failed: {e}"
    
    def _speech_to_text_whisper(self, audio_path: str) -> str:
        """Use OpenAI Whisper for STT"""
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        return transcript.text
    
    def text_to_speech(self, text: str, output_path: str = "gabriel_speech.mp3") -> str:
        """
        Convert text to speech (Text-to-Speech)
        
        Args:
            text: Text to convert
            output_path: Output audio file path
        
        Returns:
            Path to audio file
        """
        try:
            if ELEVENLABS_API_KEY:
                return self._text_to_speech_elevenlabs(text, output_path)
            else:
                return "⚠️ ElevenLabs API key not configured"
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return f"❌ Text-to-speech failed: {e}"
    
    def _text_to_speech_elevenlabs(self, text: str, output_path: str) -> str:
        """Use ElevenLabs for TTS"""
        import requests
        
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return output_path
    
    # ========================================================================
    # TRADING & MARKET ANALYSIS
    # ========================================================================
    
    def analyze_trade(self, trade_data: Dict[str, Any]) -> str:
        """
        Analyze trade with AI
        
        Args:
            trade_data: Trade information (price, volume, indicators, etc)
        
        Returns:
            Trade analysis
        """
        prompt = f"""
Analyze this ETH trade opportunity:

Entry Price: {trade_data.get('entry_price', 'N/A')} IDR
Current Price: {trade_data.get('current_price', 'N/A')} IDR
Volume: {trade_data.get('volume', 'N/A')}
RSI: {trade_data.get('rsi', 'N/A')}
MACD: {trade_data.get('macd', 'N/A')}
Trend: {trade_data.get('trend', 'N/A')}

Provide:
1. Trade opportunity assessment
2. Risk level
3. Recommended action (BUY/SELL/HOLD)
4. Stop loss & take profit levels
5. Overall confidence (0-100%)
        """
        
        context = {
            "pair": "ETH_IDR",
            "strategy": "scalper_greed_agresif",
            "timeframe": "1m"
        }
        
        return self.query(prompt, context)
    
    def get_market_advice(self, market_data: Dict[str, Any]) -> str:
        """
        Get market advice from AI
        
        Args:
            market_data: Current market data
        
        Returns:
            Market advice
        """
        prompt = f"""
Based on current market conditions, provide trading advice:

24h High: {market_data.get('high_24h', 'N/A')} IDR
24h Low: {market_data.get('low_24h', 'N/A')} IDR
Volume 24h: {market_data.get('volume_24h', 'N/A')}
Change 24h: {market_data.get('change_24h', 'N/A')}%
Volatility: {market_data.get('volatility', 'N/A')}%

Provide:
1. Current market sentiment (bullish/bearish/neutral)
2. Best trading time
3. Key support & resistance
4. Risk assessment
5. Action recommendation
        """
        
        return self.query(prompt, market_data)
    
    # ========================================================================
    # MEMORY & LEARNING
    # ========================================================================
    
    def _save_to_memory(self, category: str, data: Dict):
        """Save data to memory for learning"""
        if category not in self.memory:
            self.memory[category] = []
        
        self.memory[category].append({
            "timestamp": datetime.now().isoformat(),
            **data
        })
        
        # Keep only last 1000 entries
        if len(self.memory[category]) > 1000:
            self.memory[category] = self.memory[category][-1000:]
    
    def save_trade(self, trade_info: Dict):
        """Save trade to memory"""
        self._save_to_memory("trades", trade_info)
    
    def get_learning_summary(self) -> Dict:
        """Get learning summary"""
        return {
            "conversations": len(self.memory.get("conversations", [])),
            "trades": len(self.memory.get("trades", [])),
            "patterns": len(self.memory.get("patterns", [])),
            "model_stats": self.model_stats
        }
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    def _build_prompt(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Build enhanced prompt with context"""
        
        system = """You are GABRIEL, an advanced AI trading assistant.
        
Expertise:
- ETH scalping (aggressive strategy)
- Technical analysis
- Risk management
- Market intelligence

Be concise, actionable, and specific."""
        
        if context:
            context_str = "\n\nContext:\n"
            for k, v in context.items():
                context_str += f"• {k}: {v}\n"
            return f"{system}{context_str}\n\nUser: {prompt}"
        
        return f"{system}\n\nUser: {prompt}"
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        return {
            "model_stats": self.model_stats,
            "memory": self.get_learning_summary(),
            "priority_order": self.priority_order
        }
    
    def reset_stats(self):
        """Reset statistics"""
        for model in self.model_stats:
            self.model_stats[model] = {"success": 0, "fail": 0, "avg_time": 0}


# ============================================================================
# QUICK START EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🤖 GABRIEL - Complete LLM System")
    print("="*70)
    
    # Initialize
    gabriel = GABRIELLLMComplete(use_freellmapi=False)
    
    # 1. Simple Query
    print("\n📝 Test 1: Simple Query")
    response = gabriel.query("What's a good scalping strategy for ETH?")
    print(f"Response: {response[:200]}...")
    
    # 2. Query with context
    print("\n📊 Test 2: Query with Context")
    context = {
        "current_price": "2500 USD",
        "volatility": "2.3%",
        "trend": "bullish"
    }
    response = gabriel.query("Should I open a trade now?", context)
    print(f"Response: {response[:200]}...")
    
    # 3. Trade analysis
    print("\n🎯 Test 3: Trade Analysis")
    trade_data = {
        "entry_price": 2490,
        "current_price": 2510,
        "volume": 150000,
        "rsi": 65,
        "trend": "bullish"
    }
    response = gabriel.analyze_trade(trade_data)
    print(f"Response: {response[:200]}...")
    
    # 4. Stats
    print("\n📈 Test 4: System Stats")
    stats = gabriel.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
    
    print("\n" + "="*70)
    print("✅ GABRIEL LLM System Ready!")
    print("="*70 + "\n")
