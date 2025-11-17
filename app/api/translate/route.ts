import { NextResponse } from 'next/server';

// IndicTrans2 Python service URL (for local development)
const TRANSLATION_SERVICE_URL = process.env.TRANSLATION_SERVICE_URL || 'http://127.0.0.1:5000';

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

// Fallback translation function
function getFallbackTranslation(text: string, sourceLang: string, targetLang: string): string {
  if (sourceLang === targetLang) return text;
  
  // If translating from English to an Indic language, provide a mock response
  if (sourceLang === 'en' && targetLang in mockTranslations) {
    // Return a cleaner message indicating translation service is not available
    // Don't include the placeholder text that causes loops
    return text; // Return original text - translation will be handled in UI
  }
  
  // Otherwise return original text
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
      // Try to call the IndicTrans2 Python service
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
            timeMs: data.timeMs 
          });
        }
      } catch (fetchError) {
        console.log('Python service unavailable, using fallback:', fetchError);
      }
    }

    // Fallback: Return original text (translation service not available)
    const fallbackText = getFallbackTranslation(text, sourceLang, targetLang);
    
    return NextResponse.json({ 
      translatedText: fallbackText,
      timeMs: 0,
      isFallback: true,
      note: 'Translation service is not available. The text is returned in the original language. For full IndicTrans2 support, configure TRANSLATION_SERVICE_URL with your Python service endpoint.'
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
