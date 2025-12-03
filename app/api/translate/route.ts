import { NextResponse } from 'next/server';

const GOOGLE_TRANSLATE_API_KEY = process.env.GOOGLE_TRANSLATE_API_KEY;
const GOOGLE_TRANSLATE_URL = 'https://translation.googleapis.com/language/translate/v2';

const LANGUAGE_NAMES: Record<string, string> = {
  en: 'English',
  hi: 'Hindi',
  bn: 'Bengali',
  ta: 'Tamil',
  te: 'Telugu',
  kn: 'Kannada',
  ml: 'Malayalam',
  mr: 'Marathi',
  gu: 'Gujarati',
  pa: 'Punjabi',
  or: 'Odia',
  as: 'Assamese',
  sa: 'Sanskrit',
  sd: 'Sindhi',
  ur: 'Urdu',
  ne: 'Nepali',
  bo: 'Tibetan',
  ks: 'Kashmiri',
  mni: 'Meitei (Manipuri)',
  sat: 'Santali',
  brx: 'Bodo',
  doi: 'Dogri',
  kok: 'Konkani',
  mai: 'Maithili',
  gom: 'Konkani',
  dcc: 'Deccan',
};

const GOOGLE_LANGUAGE_CODES: Record<string, string> = {
  en: 'en',
  hi: 'hi',
  bn: 'bn',
  ta: 'ta',
  te: 'te',
  kn: 'kn',
  ml: 'ml',
  mr: 'mr',
  gu: 'gu',
  pa: 'pa',
  or: 'or',
  as: 'as',
  sa: 'sa',
  sd: 'sd',
  ur: 'ur',
  ne: 'ne',
  bo: 'bo',
  ks: 'ks',
  mni: 'mni-Mtei',
  sat: 'sat',
  brx: 'brx',
  doi: 'doi',
  kok: 'gom',
  mai: 'mai',
  gom: 'gom',
};

async function translateWithGoogleAPI(text: string, sourceLang: string, targetLang: string): Promise<string | null> {
  if (!GOOGLE_TRANSLATE_API_KEY) {
    console.error('GOOGLE_TRANSLATE_API_KEY is not configured');
    return null;
  }

  const googleSource = GOOGLE_LANGUAGE_CODES[sourceLang];
  const googleTarget = GOOGLE_LANGUAGE_CODES[targetLang];

  if (!googleSource || !googleTarget) {
    console.warn(`Google Translate does not support ${sourceLang} -> ${targetLang}`);
    return null;
  }

  const textToTranslate = text.length > 4500 ? text.slice(0, 4500) : text;

  const response = await fetch(`${GOOGLE_TRANSLATE_URL}?key=${GOOGLE_TRANSLATE_API_KEY}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      q: textToTranslate,
      source: googleSource,
      target: googleTarget,
      format: 'text',
      model: 'nmt',
    }),
    signal: AbortSignal.timeout(8000),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    console.error(`Google Translate API error: ${response.status} ${response.statusText} - ${errorBody}`);
    return null;
  }

  const data = await response.json();

  if (data.error) {
    console.error('Google Translate API returned error:', data.error);
    return null;
  }

  const translations = data?.data?.translations;

  if (!Array.isArray(translations) || !translations.length) {
    return null;
  }

  let translated = translations.map((entry: { translatedText: string }) => entry?.translatedText || '').join(' ').trim();

  if (!translated) {
    return null;
  }

  if (text.length > 4500) {
    translated += '\n\n[Note: Translation truncated to 4,500 characters to meet Google API limits]';
  }

  return translated;
}

async function translateWithMyMemory(text: string, sourceLang: string, targetLang: string): Promise<string | null> {
  try {
    const truncated = text.length > 500 ? text.slice(0, 500) : text;
    const apiUrl = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(truncated)}&langpair=${sourceLang}|${targetLang}`;

    const response = await fetch(apiUrl, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(8000),
    });

    if (!response.ok) {
      console.error(`MyMemory API error: ${response.status} ${response.statusText}`);
      return null;
    }

    const data = await response.json();

    if (data.responseStatus === 200 && data.responseData?.translatedText) {
      let translated = data.responseData.translatedText;
      if (text.length > 500) {
        translated += '\n\n[Note: Translation truncated to 500 characters due to MyMemory free tier limits]';
      }
      return translated;
    }

    return null;
  } catch (error) {
    console.error('MyMemory API error:', error);
    return null;
  }
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

    if (sourceLang === targetLang) {
      return NextResponse.json({
        translatedText: text,
        timeMs: 0,
        source: 'noop',
      });
    }

    const startTime = Date.now();
    const googleTranslation = await translateWithGoogleAPI(text, sourceLang, targetLang);

    if (googleTranslation) {
      return NextResponse.json({
        translatedText: googleTranslation,
        timeMs: Date.now() - startTime,
        source: 'google',
      });
    }

    if (sourceLang === 'en' && targetLang in LANGUAGE_NAMES) {
      const fallbackStart = Date.now();
      const cloudTranslation = await translateWithMyMemory(text, sourceLang, targetLang);

      if (cloudTranslation) {
        return NextResponse.json({
          translatedText: cloudTranslation,
          timeMs: Date.now() - fallbackStart,
          source: 'cloud-fallback',
          note: 'Google Translate unavailable, using MyMemory free tier fallback.',
        });
      }
    }

    const langName = LANGUAGE_NAMES[targetLang] || targetLang;
    return NextResponse.json(
      {
        translatedText: text,
        timeMs: 0,
        isFallback: true,
        source: 'none',
        note: `Translation unavailable for ${langName}. Returned original text.`,
      },
      { status: 503 }
    );
  } catch (error) {
    console.error('Translation error:', error);
    return NextResponse.json(
      {
        error: 'Failed to process translation',
        translatedText: 'Translation service error. Please try again.',
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  if (!GOOGLE_TRANSLATE_API_KEY) {
    return NextResponse.json(
      { status: 'unhealthy', provider: 'google', hasApiKey: false, message: 'GOOGLE_TRANSLATE_API_KEY is not set' },
      { status: 503 }
    );
  }

  return NextResponse.json({ status: 'healthy', provider: 'google', hasApiKey: true });
}
