# Google Translation Setup

This guide explains how to enable high-quality Indic translations in the Regional Narrative Engine using **Google Cloud Translation** (v2 API).

## Prerequisites

- Google Cloud project with billing enabled
- Cloud Translation API turned on
- API key (or service account) with access to the Translation API
- `.env.local` file in the project root

## 1. Enable the API and create a key

1. Visit the [Google Cloud Console](https://console.cloud.google.com/) and select your project.
2. Navigate to **APIs & Services → Library** and enable **Cloud Translation API**.
3. Go to **APIs & Services → Credentials** and create an **API key** (or reuse an existing one with Translation access).

## 2. Configure environment variables

Create (or update) `.env.local` in the project root:

```env
GOOGLE_TRANSLATE_API_KEY=your_api_key_here
```

Restart `npm run dev` (or redeploy to Vercel) so Next.js can read the variable at build time.

### Vercel deployment

1. Open your Vercel project.
2. Go to **Settings → Environment Variables**.
3. Add the same `GOOGLE_TRANSLATE_API_KEY` for the desired environments (Preview/Production).
4. Redeploy.

## 3. How translation works now

- `app/api/translate/route.ts` calls Google Cloud Translation first.
- If Google rejects the request (quota exceeded, unsupported pair, etc.), the route falls back to the free-tier **MyMemory** API for **English → Indic** translations (≈500-character limit).
- If both providers fail, the original English text is returned along with a note so the UI can inform the user.

## Supported languages

The UI allows translating English narratives into the following languages as long as Google supports them:

- Hindi (`hi`)
- Bengali (`bn`)
- Tamil (`ta`)
- Telugu (`te`)
- Kannada (`kn`)
- Malayalam (`ml`)
- Marathi (`mr`)
- Gujarati (`gu`)
- Punjabi (`pa`)
- Odia (`or`)
- Assamese (`as`)
- Urdu (`ur`)
- Nepali (`ne`)
- Sanskrit (`sa`)
- Sindhi (`sd`)
- Kashmiri (`ks`)
- Tibetan (`bo`)
- Meitei/Manipuri (`mni`)
- Dogri (`doi`)
- Santali (`sat`)
- Bodo (`brx`)
- Konkani (`kok`/`gom`)
- Maithili (`mai`)

Google recently added many of these Indic languages; if a specific code is still unsupported, the fallback path will kick in automatically.

## Legacy IndicTrans2 service (optional)

The repository still includes the previous HuggingFace/IndicTrans2 Python service (`services/translation_service.py`) and helper scripts. You can continue to run it if you need fully offline translations, but it is no longer required for default deployments.

## Troubleshooting

- **Missing translations**: Ensure `GOOGLE_TRANSLATE_API_KEY` is set in the runtime environment and the API is enabled.
- **Quota / billing errors**: Check Google Cloud console for quota usage and billing status.
- **Unsupported language**: Confirm Google supports the ISO code you are requesting; otherwise expect the MyMemory fallback (English-only).
- **Large payloads**: Google API calls are truncated to 4,500 characters to avoid exceeding the 5,000-character limit. MyMemory fallback is limited to ~500 characters.

With these steps completed, every environment (local, preview, production) will automatically use Google Cloud Translation without any additional Python services.

