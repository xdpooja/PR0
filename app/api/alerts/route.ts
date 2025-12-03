import { NextResponse } from 'next/server';

const OBSEI_URL = process.env.OBSEI_SERVICE_URL || 'http://127.0.0.1:5001';
const OBSEI_API_KEY = process.env.OBSEI_API_KEY;

export async function GET() {
  try {
    const res = await fetch(`${OBSEI_URL}/alerts`, {
      headers: OBSEI_API_KEY ? { 'x-api-key': OBSEI_API_KEY } : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      console.error('Obsei service returned error:', res.status, text);
      return NextResponse.json({ alerts: [], error: 'Bad gateway' }, { status: 502 });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    console.error('Failed to proxy to Obsei service:', err?.message || err);
    return NextResponse.json({ alerts: [], error: err?.message || 'Internal error' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { keywords, interval_seconds } = body;

    if (!Array.isArray(keywords) || keywords.length === 0) {
      return NextResponse.json({ error: 'Keywords array is required' }, { status: 400 });
    }

    const res = await fetch(`${OBSEI_URL}/start-monitor`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(OBSEI_API_KEY ? { 'x-api-key': OBSEI_API_KEY } : {}),
      },
      body: JSON.stringify({
        keywords,
        interval_seconds: interval_seconds || 300,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      console.error('Obsei start-monitor returned error:', res.status, text);
      return NextResponse.json({ error: 'Failed to start monitor' }, { status: 502 });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    console.error('Failed to start monitor:', err?.message || err);
    return NextResponse.json({ error: err?.message || 'Internal error' }, { status: 500 });
  }
}
