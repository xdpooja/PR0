import { NextResponse } from 'next/server';

const OBSEI_URL = process.env.OBSEI_SERVICE_URL || 'http://127.0.0.1:5001';

export async function GET() {
  try {
    const res = await fetch(`${OBSEI_URL}/alerts`);
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
