import { useState, useCallback } from 'react';

type LanguageCode = 'en' | 'hi' | 'bn' | 'ta' | 'te' | 'kn' | 'ml' | 'mr' | 'gu' | 'pa' | 'or' | 'as' | 'sa' | 'sd' | 'ur' | 'ne' | 'bo' | 'ks' | 'mni' | 'sat' | 'brx' | 'doi' | 'kok' | 'mai' | 'gom' | 'dcc';

export const useTranslation = () => {
  const [isTranslating, setIsTranslating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const translate = useCallback(async (text: string, sourceLang: LanguageCode, targetLang: LanguageCode) => {
    if (!text.trim()) return '';
    
    setIsTranslating(true);
    setError(null);
    
    try {
      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, sourceLang, targetLang }),
      });

      if (!response.ok) {
        throw new Error('Translation failed');
      }

      const data = await response.json();
      
      // If it's a final fallback (no service available), return original text
      // The UI will handle showing appropriate message
      if (data.isFallback && data.source === 'none') {
        return text; // Return original text when no service available
      }
      
      // Cloud translation or IndicTrans2 succeeded
      if (data.translatedText) {
        return data.translatedText;
      }
      
      // Fallback to original text if no translation received
      return text;
    } catch (err) {
      console.error('Translation error:', err);
      setError('Failed to translate text');
      return text; // Return original text on error
    } finally {
      setIsTranslating(false);
    }
  }, []);

  return { translate, isTranslating, error };
};
