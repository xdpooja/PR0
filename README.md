# The Chorus Bot

**Contextual and Conversational ROI** - AI-powered PR platform for the Indian media ecosystem

## Overview

The Chorus Bot is a comprehensive PR intelligence platform designed to solve the fragmented, multi-lingual challenges of Indian public relations. It connects media output to quantifiable business outcomes through four core AI-powered components.

## Core Features

### 1. Regional Narrative Engine
Transform one English press release into multiple culturally-nuanced regional narratives in under 30 seconds.

- **Multilingual LLM** trained on Indian regional media
- **Local Lens Adaptor** for cultural context
- **3-Step Workflow**: Source → Target → Generate

### 2. Conversion Link Attribution
The true ROI driver - prove PR's business impact with quantifiable data.

- **Source-to-Sign-Up Tracker** with unique tracking URLs
- **Analytics Integration** (Google Analytics, Mixpanel, CRM)
- **Business Impact Dashboard** showing attributed revenue

### 3. Relationship-Assist Agent
AI-powered journalist profiling with real-time social listening.

- **Hot/Warm/Cold Scoring** based on activity and history
- **Proactive Nudge System** for optimal pitch timing
- **Personalized Pitch Generator** with context awareness

### 4. Early Signal Crisis Predictor
Detect localized crisis sparks before national escalation.

- **Real-time Monitoring** across regional media and social channels
- **Risk Scoring** (0-100) with geographic/linguistic breakdown
- **Automated Response Generation** for rapid mitigation

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Icons**: Lucide React
- **Deployment**: Vercel

## Getting Started

### Prerequisites
- Node.js 18+ installed
- npm or yarn package manager

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd chorus-bot
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env.local
```

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

### Translation Configuration (Optional but Recommended)

For production-quality Indic translations, add a Google Cloud Translation API key to `.env.local`:

```env
GOOGLE_TRANSLATE_API_KEY=your_api_key_here
```

See `TRANSLATION_SETUP.md` for detailed instructions and supported languages.

### Crisis Predictor with Obsei (Production Ready)

The Crisis Predictor now includes live, AI-powered crisis detection using Obsei. Deploy it to Vercel + Render for end-to-end monitoring:

1. Deploy Obsei service to Render (see `OBSEI_DEPLOYMENT.md`)
2. Set environment variables in Vercel:
   - `OBSEI_SERVICE_URL`: Your Render service URL
   - `OBSEI_API_KEY`: Secure API key
3. The Crisis Predictor will automatically poll and display real-time alerts

For detailed deployment steps, see `OBSEI_DEPLOYMENT.md`.

### Build for Production

```bash
npm run build
npm start
```

## Deployment

### Vercel (Frontend)

This application is optimized for **Vercel deployment**:

1. Push your code to GitHub
2. Import the repository in Vercel
3. Configure environment variables (see `OBSEI_DEPLOYMENT.md`)
4. Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

### Render (Obsei Backend - Optional)

For live crisis detection, deploy the Obsei service to Render (free tier available):

1. Follow steps in `OBSEI_DEPLOYMENT.md`
2. Configure `OBSEI_SERVICE_URL` and `OBSEI_API_KEY` in Vercel environment
3. Crisis Predictor will auto-connect to live data

## Design Philosophy

The UI/UX follows SpaceX.com's design principles:

- **Minimalist aesthetic** with SF Pro Display font family
- **Dark theme** with subtle glass-effect components
- **Smooth animations** using Framer Motion
- **Data-first approach** with clear metrics and visualizations
- **Responsive design** optimized for all screen sizes

## Architecture

### Frontend-Only (Current)
- Pure Next.js application with mock data
- Static site generation for optimal performance
- API routes ready for backend integration

### Future Backend Integration
- Serverless API routes for data processing
- External services for:
  - Database (PostgreSQL with Prisma)
  - Real-time features (WebSockets/Pusher)
  - AI/ML services (OpenAI, custom models)
  - Analytics integrations

## Behavioral Principles

Each feature addresses specific psychological drivers:

| Feature | Principle | Business Impact |
|---------|-----------|-----------------|
| Crisis Predictor | Loss Aversion | Saves reputation, drives adoption |
| Conversion Attribution | Jobs-to-be-Done | Proves ROI, transforms PR to profit-driver |
| Narrative Engine | Cognitive Ease | Efficiency gain, reduces costs |
| Impact Benchmarker | Social Proof | Justifies fees, competitive advantage |

## License

Proprietary - All Rights Reserved

## Contact

For inquiries about The Chorus Bot platform, please contact the development team.
