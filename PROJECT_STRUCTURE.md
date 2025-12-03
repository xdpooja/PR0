# The Chorus Bot - Complete Project Structure & File Mapping

## 📁 Project Overview

**The Chorus Bot** is a Next.js 14 (App Router) application built with TypeScript, designed as an AI-powered PR intelligence platform for the Indian media ecosystem. It's optimized for Vercel deployment and uses a modern tech stack with static site generation.

---

## 🗂️ Complete File Structure

```
PR0/
├── app/                          # Next.js App Router directory
│   ├── api/                      # API routes (serverless functions)
│   │   └── translate/
│   │       └── route.ts         # Translation API endpoint
│   ├── conversion-attribution/
│   │   └── page.tsx              # Conversion Attribution feature page
│   ├── crisis-predictor/
│   │   └── page.tsx              # Crisis Predictor feature page
│   ├── regional-narrative/
│   │   └── page.tsx              # Regional Narrative Engine feature page
│   ├── relationship-agent/
│   │   └── page.tsx              # Relationship Agent feature page
│   ├── globals.css               # Global CSS styles
│   ├── layout.tsx                # Root layout component
│   └── page.tsx                  # Landing/home page
│
├── components/                   # Reusable React components
│   └── Navigation.tsx            # Main navigation bar component
│
├── hooks/                        # Custom React hooks
│   └── useTranslation.ts         # Translation hook for API calls
│
├── lib/                          # Utility libraries and helpers
│   ├── indic-translator.ts       # Legacy IndicTrans2 translator stub (unused)
│   └── utils.ts                  # Utility functions (formatting, etc.)
│
├── services/                     # External service integrations
│   └── translation_service.py    # Legacy IndicTrans2 Python service
│
├── scripts/                      # Setup and installation scripts
│   └── install_indic_trans2.sh  # Legacy IndicTrans2 installation script
│
├── public/                       # Static assets
│   └── robots.txt                # SEO robots file
│
├── Configuration Files
│   ├── package.json              # Node.js dependencies and scripts
│   ├── package-lock.json         # Dependency lock file
│   ├── tsconfig.json             # TypeScript configuration
│   ├── next.config.js            # Next.js configuration
│   ├── tailwind.config.ts        # TailwindCSS configuration
│   ├── postcss.config.mjs        # PostCSS configuration
│   └── vercel.json               # Vercel deployment configuration
│
└── Documentation
    ├── README.md                  # Main project documentation
    ├── PROJECT_SUMMARY.md        # Project summary and features
    ├── DEPLOYMENT.md             # Deployment instructions
    ├── TRANSLATION_SETUP.md      # Translation service setup guide
    ├── DEPENDENCIES.txt          # Dependency list
    └── requirements.txt           # Python dependencies
```

---

## 📄 Detailed File Descriptions

### 🎯 **Core Application Files**

#### **`app/layout.tsx`** - Root Layout
- **Purpose**: Defines the root HTML structure for all pages
- **Key Features**:
  - Sets up HTML document structure (`<html>`, `<body>`)
  - Imports global CSS styles
  - Includes `<Navigation />` component on all pages
  - Sets metadata (title, description) for SEO
- **Connections**:
  - Imports: `@/components/Navigation` (Navigation component)
  - Imports: `./globals.css` (Global styles)
  - Wraps: All page components via `{children}`

#### **`app/page.tsx`** - Landing Page
- **Purpose**: Main landing/home page with hero section and feature overview
- **Key Features**:
  - Hero section with animated starfield background
  - "The Hair-on-Fire Problem" section with behavioral principles
  - Four core features preview cards
  - Testimonial carousel
  - Sign-up section
- **Connections**:
  - Uses: `framer-motion` for animations
  - Uses: `lucide-react` for icons
  - Links to: `/conversion-attribution`, `/regional-narrative`, `/relationship-agent`, `/crisis-predictor`
- **Data Flow**: Static content (no API calls)

#### **`app/globals.css`** - Global Styles
- **Purpose**: Global CSS styles and TailwindCSS directives
- **Key Features**:
  - TailwindCSS base, components, utilities
  - CSS variables for theme colors
  - Custom classes (`.glass-effect`, `.text-gradient`)
  - System font stack configuration
- **Connections**:
  - Imported by: `app/layout.tsx`
  - Used by: All components via TailwindCSS classes

---

### 🧭 **Navigation & Components**

#### **`components/Navigation.tsx`** - Navigation Bar
- **Purpose**: Fixed navigation bar with links to all features
- **Key Features**:
  - Fixed position at top of page
  - Responsive mobile menu
  - Active route highlighting
  - Scroll-based background opacity change
- **Connections**:
  - Uses: `next/navigation` (`usePathname` hook)
  - Uses: `framer-motion` for animations
  - Links to: All feature pages
  - Included in: `app/layout.tsx` (rendered on all pages)

---

### 🎨 **Feature Pages**

#### **`app/regional-narrative/page.tsx`** - Regional Narrative Engine
- **Purpose**: 3-step workflow for generating multilingual press releases
- **Key Features**:
  - **Step 1**: Source content ingestion with auto-summarize toggle
  - **Step 2**: Contextual targeting (region, language, media type, tone, word count)
  - **Step 3**: Side-by-side comparison with refinement options
- **Connections**:
  - Uses: `@/hooks/useTranslation` (Translation hook)
  - Calls: `/api/translate` (Translation API)
  - State Management: React `useState` for multi-step workflow
- **Data Flow**:
  ```
  User Input → State → Translation Hook → API Route → Python Service (optional)
  ```

#### **`app/conversion-attribution/page.tsx`** - Conversion Attribution Dashboard
- **Purpose**: ROI tracking dashboard showing PR impact on business metrics
- **Key Features**:
  - Integration status panel (Google Analytics, Mixpanel, CRM)
  - Key metrics cards (attributed value, conversions, conversion rate)
  - Trend visualization charts (Recharts)
  - Placement performance table
  - Conversion rate benchmarker
  - Create tracking link modal
- **Connections**:
  - Uses: `recharts` for data visualization
  - Uses: `@/lib/utils.ts` for currency formatting
  - Data: Currently uses mock data (ready for API integration)

#### **`app/relationship-agent/page.tsx`** - Relationship-Assist Agent
- **Purpose**: AI-powered journalist profiling with pitch timing recommendations
- **Key Features**:
  - Priority nudge system (hot/warm/cold scoring)
  - Contact cards with impact scores
  - Search and filter functionality
  - Detailed contact profile modal
  - AI-synthesized pitch recommendations
- **Connections**:
  - Data: Currently uses mock data (ready for API integration)
  - Future: Will connect to social media APIs (X/Twitter, LinkedIn)

#### **`app/crisis-predictor/page.tsx`** - Early Signal Crisis Predictor
- **Purpose**: Real-time crisis detection and risk monitoring
- **Key Features**:
  - Global risk score dashboard
  - Local spark alerts with risk scoring (0-100)
  - Active threats vs. mitigation history toggle
  - Detailed alert analysis (sentiment, keywords, geographic mapping)
  - AI-recommended mitigation actions
  - One-click holding statement generation
- **Connections**:
  - Data: Currently uses mock data (ready for API integration)
  - Future: Will connect to social media monitoring APIs

---

### 🔌 **API Routes**

#### **`app/api/translate/route.ts`** - Translation API Endpoint
- **Purpose**: Serverless API route for text translation
- **Key Features**:
  - POST endpoint for translation requests
  - GET endpoint for health checks
  - Calls Google Cloud Translation v2 using `GOOGLE_TRANSLATE_API_KEY`
  - Falls back to the MyMemory free tier (English → Indic) when Google is unavailable
- **Connections**:
  - Called by: `hooks/useTranslation.ts`
  - Environment: Requires `GOOGLE_TRANSLATE_API_KEY`
  - Optional legacy: can be extended to call the IndicTrans2 Python service, but this is no longer default
- **Data Flow**:
  ```
  Frontend → useTranslation Hook → /api/translate → Google Cloud Translation (→ MyMemory fallback)
  ```

---

### 🪝 **Custom Hooks**

#### **`hooks/useTranslation.ts`** - Translation Hook
- **Purpose**: React hook for managing translation API calls
- **Key Features**:
  - Manages translation state (loading, error)
  - Handles API calls to `/api/translate`
  - Returns translated text or original on error
- **Connections**:
  - Used by: `app/regional-narrative/page.tsx`
  - Calls: `app/api/translate/route.ts`
- **Usage Pattern**:
  ```typescript
  const { translate, isTranslating, error } = useTranslation();
  const translated = await translate(text, 'en', 'hi');
  ```

---

### 🛠️ **Utility Libraries**

#### **`lib/utils.ts`** - Utility Functions
- **Purpose**: Shared utility functions for formatting and common operations
- **Key Functions**:
  - `cn()`: Class name merging utility (clsx + tailwind-merge)
  - `formatCurrency()`: Format numbers as Indian Rupees (₹XK, ₹XL)
  - `formatDate()`: Format dates in Indian locale
  - `getRelativeTime()`: Get relative time strings ("2 days ago")
- **Connections**:
  - Used by: Multiple feature pages for data formatting
  - Dependencies: `clsx`, `tailwind-merge`

#### **`lib/indic-translator.ts`** - Legacy Translator Stub
- **Purpose**: Previously wrapped the IndicTrans2 model; now kept for reference
- **Key Notes**:
  - Contains placeholder initialization/translate methods
  - Not imported anywhere in the current Google-based flow
  - Safe to remove once the legacy pipeline is retired

---

### 🐍 **Python Services**

#### **`services/translation_service.py`** - Legacy IndicTrans2 Service
- **Purpose**: Original Flask service hosting HuggingFace IndicTrans2 models
- **Status**: Optional / deprecated in favor of Google Cloud Translation
- **When to use**: Only if you need an offline/self-hosted translation stack
- **Setup**: Refer to historical instructions in `scripts/install_indic_trans2.sh`

---

### ⚙️ **Configuration Files**

#### **`package.json`** - Node.js Dependencies
- **Purpose**: Defines project dependencies and npm scripts
- **Key Dependencies**:
  - `next`: Next.js framework (^14.2.0)
  - `react`, `react-dom`: React library (^18.3.0)
  - `framer-motion`: Animation library (^11.0.0)
  - `recharts`: Chart library (^2.12.0)
  - `lucide-react`: Icon library (^0.263.1)
  - `tailwindcss`: CSS framework (^3.4.0)
- **Scripts**:
  - `npm run dev`: Start development server
  - `npm run build`: Build for production
  - `npm start`: Start production server
  - `npm run lint`: Run ESLint

#### **`tsconfig.json`** - TypeScript Configuration
- **Purpose**: TypeScript compiler options
- **Key Settings**:
  - Target: ES2017
  - Module: ESNext
  - JSX: Preserve (for Next.js)
  - Path aliases: `@/*` → `./*`
  - Strict mode enabled

#### **`next.config.js`** - Next.js Configuration
- **Purpose**: Next.js framework configuration
- **Key Settings**:
  - React strict mode enabled
  - SWC minification enabled
- **Note**: Minimal config (Next.js auto-detects most settings)

#### **`tailwind.config.ts`** - TailwindCSS Configuration
- **Purpose**: TailwindCSS utility class configuration
- **Key Settings**:
  - Content paths (where to scan for classes)
  - Custom animations (fade-in, slide-up, scale-in)
  - System font stack
  - CSS variable integration

#### **`vercel.json`** - Vercel Deployment Configuration
- **Purpose**: Vercel platform-specific settings
- **Key Settings**:
  - Build command: `next build`
  - Output directory: `.next`
  - Framework: Next.js
  - Rewrites: All routes to `/` (for SPA behavior)

#### **`postcss.config.mjs`** - PostCSS Configuration
- **Purpose**: PostCSS processing for TailwindCSS
- **Key Settings**:
  - TailwindCSS plugin
  - Autoprefixer plugin

---

### 📜 **Scripts**

#### **`scripts/install_indic_trans2.sh`** - Legacy Installation Script
- **Purpose**: Bootstraps the IndicTrans2 Python stack (no longer required for Google Cloud Translation)
- **Usage**: Only needed if you revive the legacy service

---

### 📚 **Documentation Files**

#### **`README.md`** - Main Documentation
- **Purpose**: Project overview, features, and getting started guide
- **Contents**: Overview, core features, tech stack, installation, deployment

#### **`PROJECT_SUMMARY.md`** - Project Summary
- **Purpose**: Detailed summary of what has been built
- **Contents**: Features implemented, technical architecture, build results, next steps

#### **`DEPLOYMENT.md`** - Deployment Guide
- **Purpose**: Step-by-step deployment instructions
- **Contents**: Vercel deployment, environment variables, troubleshooting

#### **`TRANSLATION_SETUP.md`** - Translation Setup Guide
- **Purpose**: Explains how to configure Google Cloud Translation (and mentions the legacy IndicTrans2 option)
- **Contents**: API key creation, environment variables, supported languages, fallback behavior

---

## 🔗 File Connection Map

### **Frontend Flow**
```
app/layout.tsx
  ├── components/Navigation.tsx (imported)
  ├── app/globals.css (imported)
  └── app/page.tsx (children)
      └── Links to feature pages

app/regional-narrative/page.tsx
  ├── hooks/useTranslation.ts (imported)
  │   └── app/api/translate/route.ts (calls Google + fallback)
  └── lib/utils.ts (imported for formatting)

app/conversion-attribution/page.tsx
  ├── lib/utils.ts (imported for currency formatting)
  └── recharts (for charts)

app/relationship-agent/page.tsx
  └── (uses mock data, ready for API integration)

app/crisis-predictor/page.tsx
  └── (uses mock data, ready for API integration)
```

### **Backend Flow**
```
services/translation_service.py
  └── (Python service, runs independently)
      └── Called by app/api/translate/route.ts
```

### **Configuration Flow**
```
package.json
  ├── Defines dependencies
  ├── Defines scripts
  └── Used by npm/yarn

tsconfig.json
  └── TypeScript compiler uses this

next.config.js
  └── Next.js uses this for build

tailwind.config.ts
  └── TailwindCSS uses this for class generation

vercel.json
  └── Vercel uses this for deployment
```

---

## 🎯 Key Architectural Patterns

### **1. Next.js App Router Structure**
- **File-based routing**: Each folder in `app/` becomes a route
- **Layout nesting**: `app/layout.tsx` wraps all pages
- **Server Components**: Default (can use `"use client"` for interactivity)

### **2. Component Organization**
- **Feature-based**: Each feature has its own page
- **Shared components**: `components/` for reusable UI
- **Custom hooks**: `hooks/` for reusable logic

### **3. API Integration Pattern**
```
Frontend Component
  → Custom Hook (useTranslation)
    → API Route (/api/translate)
      → External Service (Python) or Fallback
```

### **4. Styling Approach**
- **TailwindCSS**: Utility-first CSS framework
- **Global styles**: `app/globals.css` for base styles
- **Custom classes**: Defined in `globals.css` (`.glass-effect`, etc.)
- **Animations**: Framer Motion for complex animations

### **5. State Management**
- **Local state**: React `useState` for component-level state
- **No global state**: Currently no Redux/Zustand (can be added if needed)
- **Server state**: Ready for React Query/SWR integration

---

## 🚀 Data Flow Examples

### **Example 1: Translation Flow**
```
1. User enters text in app/regional-narrative/page.tsx
2. User selects target language
3. Component calls useTranslation hook
4. Hook calls POST /api/translate
5. API route checks for Python service
6. If available: Calls Python service
7. If not: Returns mock translation
8. Hook returns translated text
9. Component updates UI with translation
```

### **Example 2: Navigation Flow**
```
1. User clicks link in components/Navigation.tsx
2. Next.js router navigates to new page
3. app/layout.tsx wraps the new page
4. Navigation component highlights active route
5. Feature page renders with its content
```

### **Example 3: Styling Flow**
```
1. Component uses TailwindCSS classes
2. TailwindCSS scans component files (via tailwind.config.ts)
3. Generates CSS from used classes
4. app/globals.css includes TailwindCSS directives
5. Styles applied to component
```

---

## 🔄 Future Integration Points

### **Ready for Backend Integration**
1. **API Routes**: `app/api/` directory ready for new endpoints
2. **Database**: Can add Prisma/TypeORM for database access
3. **Authentication**: Can add NextAuth.js for user auth
4. **Real-time**: Can add WebSockets/Pusher for live updates

### **External Services Ready**
1. **Translation**: Python service already set up
2. **Analytics**: Google Analytics/Mixpanel integration points defined
3. **Social Media**: API connection points in relationship-agent page
4. **Crisis Monitoring**: API connection points in crisis-predictor page

---

## 📊 Build & Deployment

### **Build Process**
```
npm run build
  → TypeScript compilation (tsconfig.json)
  → Next.js build (next.config.js)
  → TailwindCSS processing (tailwind.config.ts)
  → Static page generation
  → Output to .next/ directory
```

### **Deployment Process**
```
Vercel detects Next.js
  → Reads vercel.json
  → Runs npm run build
  → Deploys .next/ output
  → Serves static pages + API routes
```

---

## 🎨 Design System

### **Color Scheme**
- **Background**: Black (#000000)
- **Foreground**: White (#ffffff)
- **Accents**: Gray scale (gray-400, gray-500, etc.)
- **Highlights**: Blue, Green, Red for status indicators

### **Typography**
- **Font**: System fonts (SF Pro on macOS, Segoe UI on Windows)
- **Weights**: Light (300), Regular (400), Medium (500)
- **Sizes**: Responsive (text-5xl on desktop, text-3xl on mobile)

### **Components**
- **Glass Effect**: `.glass-effect` class (semi-transparent with blur)
- **Animations**: Framer Motion for smooth transitions
- **Icons**: Lucide React icon library

---

## ✅ Summary

This is a **well-structured, production-ready Next.js application** with:
- ✅ Clear separation of concerns
- ✅ Modular component architecture
- ✅ API routes ready for backend integration
- ✅ Comprehensive documentation
- ✅ Optimized for Vercel deployment
- ✅ TypeScript for type safety
- ✅ Modern UI with TailwindCSS and Framer Motion

The codebase is **scalable** and **maintainable**, with clear file organization and connection patterns that make it easy to understand and extend.

