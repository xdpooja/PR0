import { NextResponse } from 'next/server';

// IndicTrans2 Python service URL (for local development)
const TRANSLATION_SERVICE_URL = process.env.TRANSLATION_SERVICE_URL || 'http://127.0.0.1:5000';

// Language code mapping for translation APIs (ISO 639-1 to full language names)
const LANGUAGE_NAMES: Record<string, string> = {
  'hi': 'hindi',
  'bn': 'bengali',
  'ta': 'tamil',
  'te': 'telugu',
  'kn': 'kannada',
  'ml': 'malayalam',
  'mr': 'marathi',
  'gu': 'gujarati',
  'pa': 'punjabi',
  'or': 'oriya',
  'as': 'assamese',
  'ur': 'urdu',
  'ne': 'nepali',
  'sa': 'sanskrit',
  'mni': 'manipuri',
};

// Mock translation responses for when IndicTrans2 service is unavailable
const mockTranslations: Record<string, string> = {
  'hi': 'हिंदी में अनुवादित पाठ',
  'bn': 'বাংলায় অনুবাদ করা পাঠ্য',
  'ta': 'தமிழில் மொழிபெயர்க்கப்பட்ட உரை',
  'te': 'తెలుగులో అనువదించిన పాఠ్యం',
  'kn': 'ಕನ್ನಡದಲ್ಲಿ ಅನುವಾದಿಸಿದ ಪಠ್ಯ',
  'ml': 'മലയാളത്തിൽ അനുവദിച്ച വാചകം',
  'mr': 'मराठीत अनुवादित मजकूर',
  'gu': 'ગુજરાતીમાં અનુવાદિત ટેક્સ્ટ',
  'pa': 'ਪੰਜਾਬੀ ਵਿੱਚ ਅਨੁਵਾਦਿਤ ਟੈਕਸਟ',
  'or': 'ଓଡ଼ିଆରେ ଅନୁବାଦିତ ପାଠ୍ୟ',
  'as': 'অসমীয়াত অনুবাদ কৰা পাঠ',
  'ur': 'اردو میں ترجمہ شدہ متن',
  'ne': 'नेपालीमा अनुवाद गरिएको पाठ',
  'sa': 'संस्कृत में अनुवादित पाठ',
  'mni': 'মনিপুরীত অনুবাদ কৰা পাঠ',
};

// Cloud translation fallback using MyMemory Translation API (free tier)
async function translateWithCloudAPI(text: string, sourceLang: string, targetLang: string): Promise<string | null> {
  try {
    // MyMemory Translation API free tier (supports Indic languages)
    // API uses ISO 639-1 codes directly (e.g., 'en|hi' for English to Hindi)
    // For languages that might have issues, we map to full names
    const langCodeMap: Record<string, string> = {
      'or': 'or', // Odia
      'mni': 'mni', // Manipuri might need special handling
    };
    
    const sourceCode = sourceLang === 'en' ? 'en' : langCodeMap[sourceLang] || sourceLang;
    const targetCode = langCodeMap[targetLang] || targetLang;
    
    // Limit text length to 500 characters for free tier
    const textToTranslate = text.length > 500 ? text.substring(0, 500) : text;

    const apiUrl = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(textToTranslate)}&langpair=${sourceCode}|${targetCode}`;
    
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: AbortSignal.timeout(8000), // 8 second timeout
    });

    if (!response.ok) {
      console.error(`MyMemory API error: ${response.status} ${response.statusText}`);
      return null;
    }

    const data = await response.json();
    
    if (data.responseStatus === 200 && data.responseData?.translatedText) {
      let translated = data.responseData.translatedText;
      
      // If we truncated the text, note it
      if (text.length > 500) {
        translated += '\n\n[Note: Translation truncated to 500 characters due to free tier limits]';
      }
      
      return translated;
    }

    if (data.responseStatus === 403) {
      console.error('MyMemory API: Daily limit reached');
    }

    return null;
  } catch (error) {
    console.error('Cloud translation API error:', error);
    return null;
  }
}

// Fallback translation function
function getFallbackTranslation(text: string, sourceLang: string, targetLang: string): string {
  if (sourceLang === targetLang) return text;
  
  // Return original text - cloud translation will be handled in the main function
  return text;
}

export async function POST(req: Request) {
  try {
    const { text, sourceLang, targetLang } = await req.json();
    
    if (!text || !sourceLang || !targetLang) {
      return NextResponse.json(
        { error: 'Missing required fields: text, sourceLang, targetLang' },
        { status: 400 }
      );
    }

    // Check if translation service URL is available and not localhost (for production)
    const usePythonService = TRANSLATION_SERVICE_URL && 
                              !TRANSLATION_SERVICE_URL.includes('127.0.0.1') && 
                              !TRANSLATION_SERVICE_URL.includes('localhost');

    if (usePythonService) {
      // Try to call the IndicTrans2 Python service first
      try {
        const response = await fetch(`${TRANSLATION_SERVICE_URL}/translate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text,
            sourceLang,
            targetLang,
          }),
          // Add timeout for serverless environments
          signal: AbortSignal.timeout(10000), // 10 second timeout
        });

        if (response.ok) {
          const data = await response.json();
          return NextResponse.json({ 
            translatedText: data.translatedText,
            timeMs: data.timeMs,
            source: 'indictrans2'
          });
        }
      } catch (fetchError) {
        console.log('Python service unavailable, trying cloud API:', fetchError);
      }
    }

    // Fallback: Try cloud translation API (MyMemory - free tier)
    if (sourceLang === 'en' && targetLang in LANGUAGE_NAMES) {
      const startTime = Date.now();
      const cloudTranslation = await translateWithCloudAPI(text, sourceLang, targetLang);
      
      if (cloudTranslation && cloudTranslation !== text) {
        const timeMs = Date.now() - startTime;
        return NextResponse.json({ 
          translatedText: cloudTranslation,
          timeMs,
          source: 'cloud',
          note: 'Using cloud translation API (free tier). For best quality IndicTrans2 translations, configure TRANSLATION_SERVICE_URL with your Python service endpoint.'
        });
      }
    }

    // Final fallback: Return original text with message
    const fallbackText = getFallbackTranslation(text, sourceLang, targetLang);
    
    return NextResponse.json({ 
      translatedText: fallbackText,
      timeMs: 0,
      isFallback: true,
      source: 'none',
      note: 'Translation service is not available. The text is returned in the original language. For full translation support, configure TRANSLATION_SERVICE_URL with your Python service endpoint or enable cloud translation.'
    });
    
  } catch (error) {
    console.error('Translation error:', error);
    
    // Return a generic fallback
    return NextResponse.json(
      { 
        error: 'Failed to process translation',
        translatedText: 'Translation service error. Please try again.'
      },
      { status: 500 }
    );
  }
}

// Health check endpoint
export async function GET() {
  try {
    const response = await fetch(`${TRANSLATION_SERVICE_URL}/health`);
    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { status: 'unhealthy', error: 'Translation service unavailable' },
      { status: 503 }
    );
  }
}
