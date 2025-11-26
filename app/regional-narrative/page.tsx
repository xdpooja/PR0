"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Upload, FileText, Sparkles, Copy, Check, RefreshCw, Send, Mail, Users, Globe, Languages } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";

export default function RegionalNarrative() {
  const [step, setStep] = useState(1);
  const [sourceText, setSourceText] = useState("");
  const [selectedRegion, setSelectedRegion] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("");
  const [selectedMediaType, setSelectedMediaType] = useState("");
  const [tonePreset, setTonePreset] = useState("formal");
  const [wordCount, setWordCount] = useState(250);
  const [generatedText, setGeneratedText] = useState("");
  const [originalGeneratedText, setOriginalGeneratedText] = useState(""); // Store original English text
  const [copied, setCopied] = useState(false);
  const [autoSummarize, setAutoSummarize] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailSubject, setEmailSubject] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [extractedEmails, setExtractedEmails] = useState<string[]>([]);
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationProgress, setTranslationProgress] = useState(0);
  const lastTranslatedLangRef = useRef<string>(""); // Track last translated language to prevent loops
  const hasShownTranslationNoteRef = useRef<boolean>(false); // Track if we've shown the translation note
  
  // Initialize translation hook
  const { translate: translateText, isTranslating: isTranslationInProgress } = useTranslation();
  
  // Available languages for translation (aligned with IndicTrans2 backend support)
  const supportedLanguages = [
    { code: 'hi', name: 'Hindi' },
    { code: 'bn', name: 'Bengali' },
    { code: 'ta', name: 'Tamil' },
    { code: 'te', name: 'Telugu' },
    { code: 'kn', name: 'Kannada' },
    { code: 'ml', name: 'Malayalam' },
    { code: 'mr', name: 'Marathi' },
    { code: 'gu', name: 'Gujarati' },
    { code: 'pa', name: 'Punjabi' },
    { code: 'or', name: 'Odia' },
    { code: 'as', name: 'Assamese' },
    { code: 'ur', name: 'Urdu' },
    { code: 'ne', name: 'Nepali' },
    { code: 'sa', name: 'Sanskrit' },
    { code: 'mni', name: 'Manipuri' },
  ];
  
  // Handle translation
  const handleTranslate = useCallback(async (text: string, targetLang: string) => {
    if (!text || !targetLang || targetLang === 'en') return text;
    
    // Check if this is placeholder text or error message to avoid re-translating
    if (text.includes('[Translation placeholder') || 
        text.includes('[Note: Translation service') ||
        text.includes('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')) {
      return text;
    }
    
    try {
      setIsTranslating(true);
      setTranslationProgress(30);
      
      const translatedText = await translateText(text, 'en' as const, targetLang as any);
      
      setTranslationProgress(100);
      setTimeout(() => setTranslationProgress(0), 500);
      
      // Check if we got a valid translation (different from original and not an error message)
      if (!translatedText || translatedText === text) {
        // If translation is same as original, service likely not available
        const langName = supportedLanguages.find(l => l.code === targetLang)?.name || targetLang;
        return `${text}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n[Note: Translation service is not available. The narrative above is in English. For full ${langName} translation support, configure the IndicTrans2 service or ensure cloud translation is enabled.]`;
      }
      
      // Check if it's already an error message (to avoid adding it twice)
      if (translatedText.includes('[Note: Translation service')) {
        return translatedText;
      }
      
      // Valid translation received
      return translatedText;
    } catch (error) {
      console.error('Translation error:', error);
      const langName = supportedLanguages.find(l => l.code === targetLang)?.name || targetLang;
      return `${text}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n[Note: Translation service error. The narrative above is in English. For full ${langName} translation support, configure the IndicTrans2 service or check cloud translation API.]`;
    } finally {
      setIsTranslating(false);
    }
  }, [translateText, supportedLanguages]);
  
  // Auto-translate generated text when language changes (but not when generatedText changes)
  useEffect(() => {
    // Only translate if:
    // 1. We have original generated text
    // 2. Language is selected and not English
    // 3. Language has actually changed (not just generatedText)
    // 4. We haven't already translated to this language
    if (originalGeneratedText && selectedLanguage && selectedLanguage !== 'en' && lastTranslatedLangRef.current !== selectedLanguage) {
      const translateContent = async () => {
        lastTranslatedLangRef.current = selectedLanguage;
        hasShownTranslationNoteRef.current = false; // Reset note flag for new language
        const translated = await handleTranslate(originalGeneratedText, selectedLanguage);
        setGeneratedText(translated);
        // Check if translation added a note
        if (translated.includes('[Note: Translation service')) {
          hasShownTranslationNoteRef.current = true;
        }
      };
      
      translateContent();
    } else if (selectedLanguage === 'en' && originalGeneratedText) {
      // If switching back to English, show original (without translation notes)
      setGeneratedText(originalGeneratedText);
      lastTranslatedLangRef.current = 'en';
      hasShownTranslationNoteRef.current = false;
    }
  }, [selectedLanguage, originalGeneratedText, handleTranslate]);

  const regions = [
    { name: "North India", languages: ['hi', 'pa', 'ur', 'ne'] },
    { name: "South India", languages: ['ta', 'te', 'kn', 'ml'] },
    { name: "East India", languages: ['bn', 'or', 'as'] },
    { name: "West India", languages: ['mr', 'gu'] },
    { name: "North East India", languages: ['as', 'mni'] }
  ];
  
  // Update selected region's available languages
  const availableLanguages = selectedRegion 
    ? supportedLanguages.filter(lang => 
        regions.find(r => r.name === selectedRegion)?.languages.includes(lang.code)
      )
    : [];
    
  // Handle region change
  const handleRegionChange = (region: string) => {
    setSelectedRegion(region);
    // Reset language when region changes
    setSelectedLanguage('');
  };

  const mediaTypes = ["Financial Daily", "Tech Blog", "Consumer Magazine", "Policy Journal", "Lifestyle Publication"];
  const tonePresets = [
    { value: "formal", label: "Formal" },
    { value: "urgent", label: "Urgent/Crisis" },
    { value: "engaging", label: "B2C/Engaging" },
    { value: "analytical", label: "Policy-Driven/Analytical" },
  ];

  // Generate narrative based on source text and parameters
  const generateNarrative = (source: string, mediaType: string, tone: string, targetWords: number, region: string): string => {
    if (!source || !source.trim()) {
      return "Please provide source text to generate a narrative.";
    }

    // Extract key information from source text
    const sourceLower = source.toLowerCase();
    const words = source.split(/\s+/).filter(w => w.length > 0);
    const sourceLength = words.length;
    
    // Determine content type from source
    let contentTheme = "announcement";
    if (sourceLower.includes("launch") || sourceLower.includes("release")) contentTheme = "product launch";
    if (sourceLower.includes("partnership") || sourceLower.includes("collaboration")) contentTheme = "partnership";
    if (sourceLower.includes("funding") || sourceLower.includes("investment")) contentTheme = "funding";
    if (sourceLower.includes("award") || sourceLower.includes("recognition")) contentTheme = "achievement";
    if (sourceLower.includes("crisis") || sourceLower.includes("issue")) contentTheme = "crisis management";
    
    // Extract key points (simple extraction - first few sentences or bullet points)
    const sentences = source.split(/[.!?]+/).filter(s => s.trim().length > 10);
    const keyPoints = sentences.slice(0, Math.min(5, sentences.length));
    
    // Generate tone-appropriate opening
    let opening = "";
    if (tone === "urgent") {
      opening = "BREAKING: ";
    } else if (tone === "engaging") {
      opening = "Exciting news from ";
    } else if (tone === "analytical") {
      opening = "Analysis: ";
    }
    
    // Regional context based on selected region
    const regionContext: Record<string, string> = {
      "North India": "Northern markets",
      "South India": "Southern regions",
      "East India": "Eastern states",
      "West India": "Western markets",
      "North East India": "Northeastern states"
    };
    const regionName = regionContext[region] || "regional markets";
    
    // Media type specific formatting
    let narrative = "";
    if (mediaType === "Financial Daily") {
      narrative = `${opening}${contentTheme.charAt(0).toUpperCase() + contentTheme.slice(1)} Impact on ${regionName}\n\n`;
      narrative += `Key Highlights:\n`;
      keyPoints.forEach((point, idx) => {
        if (point.trim()) narrative += `• ${point.trim()}\n`;
      });
      narrative += `\nMarket Analysis:\n`;
      narrative += `This development represents a significant shift in ${regionName.toLowerCase()}, with implications for local businesses and consumers. The strategic move aligns with broader economic trends and regional growth patterns.\n\n`;
    } else if (mediaType === "Tech Blog") {
      narrative = `${opening}Tech Innovation in ${regionName}\n\n`;
      narrative += `What's New:\n`;
      keyPoints.slice(0, 3).forEach((point, idx) => {
        if (point.trim()) narrative += `• ${point.trim()}\n`;
      });
      narrative += `\nWhy It Matters:\n`;
      narrative += `This innovation addresses key challenges in ${regionName.toLowerCase()} and opens new possibilities for tech adoption and digital transformation.\n\n`;
    } else if (mediaType === "Consumer Magazine") {
      narrative = `${opening}What This Means for You in ${regionName}\n\n`;
      narrative += `Highlights:\n`;
      keyPoints.slice(0, 4).forEach((point, idx) => {
        if (point.trim()) narrative += `• ${point.trim()}\n`;
      });
      narrative += `\nConsumer Impact:\n`;
      narrative += `Residents of ${regionName.toLowerCase()} can expect improved services and new opportunities as this initiative rolls out across the region.\n\n`;
    } else if (mediaType === "Policy Journal") {
      narrative = `${opening}Policy Implications for ${regionName}\n\n`;
      narrative += `Key Points:\n`;
      keyPoints.forEach((point, idx) => {
        if (point.trim()) narrative += `• ${point.trim()}\n`;
      });
      narrative += `\nPolicy Analysis:\n`;
      narrative += `This development requires careful consideration of regulatory frameworks and policy alignment to ensure sustainable growth in ${regionName.toLowerCase()}.\n\n`;
    } else if (mediaType === "Lifestyle Publication") {
      narrative = `${opening}Lifestyle Impact in ${regionName}\n\n`;
      narrative += `What's Changing:\n`;
      keyPoints.slice(0, 3).forEach((point, idx) => {
        if (point.trim()) narrative += `• ${point.trim()}\n`;
      });
      narrative += `\nLifestyle Benefits:\n`;
      narrative += `This brings exciting changes to daily life in ${regionName.toLowerCase()}, enhancing convenience and quality of life for residents.\n\n`;
    } else {
      // Default format
      narrative = `${opening}${contentTheme.charAt(0).toUpperCase() + contentTheme.slice(1)} in ${regionName}\n\n`;
      narrative += `Key Points:\n`;
      keyPoints.forEach((point, idx) => {
        if (point.trim()) narrative += `• ${point.trim()}\n`;
      });
      narrative += `\nRegional Context:\n`;
      narrative += `This development has significant implications for ${regionName.toLowerCase()}, reflecting broader trends and opportunities in the region.\n\n`;
    }
    
    // Add tone-specific closing
    if (tone === "urgent") {
      narrative += `Immediate action required. Stakeholders should prepare for rapid changes in the coming weeks.`;
    } else if (tone === "engaging") {
      narrative += `This is an exciting time for ${regionName.toLowerCase()}, with more developments expected soon.`;
    } else if (tone === "analytical") {
      narrative += `Further analysis is needed to fully understand the long-term implications for ${regionName.toLowerCase()}.`;
    } else {
      narrative += `This represents a significant milestone for ${regionName.toLowerCase()} and sets the stage for future growth.`;
    }
    
    // Adjust length to match target word count (rough approximation)
    const currentWords = narrative.split(/\s+/).length;
    if (currentWords < targetWords * 0.7) {
      // Add more content if too short
      const additionalContent = `\n\nAdditional Context:\nThe regional implementation strategy focuses on local needs and cultural sensitivities. Community engagement and stakeholder consultation have been key priorities in ensuring successful adoption across ${regionName.toLowerCase()}.`;
      narrative += additionalContent;
    }
    
    // Truncate if too long (rough approximation)
    const finalWords = narrative.split(/\s+/);
    if (finalWords.length > targetWords * 1.2) {
      narrative = finalWords.slice(0, Math.floor(targetWords * 1.1)).join(' ') + '...';
    }
    
    return narrative.trim();
  };

  const handleGenerate = async () => {
    if (!sourceText || !sourceText.trim()) {
      alert("Please enter source text first.");
      return;
    }
    
    // Generate English narrative based on actual source text and parameters
    const englishNarrative = generateNarrative(
      sourceText,
      selectedMediaType,
      tonePreset,
      wordCount,
      selectedRegion
    );
    
    // Store original English text
    setOriginalGeneratedText(englishNarrative);
    lastTranslatedLangRef.current = ""; // Reset translation tracking
    hasShownTranslationNoteRef.current = false; // Reset note flag
    
    // If a non-English language is selected, translate it
    if (selectedLanguage && selectedLanguage !== 'en') {
      setIsTranslating(true);
      const translated = await handleTranslate(englishNarrative, selectedLanguage);
      setGeneratedText(translated);
      lastTranslatedLangRef.current = selectedLanguage;
      if (translated.includes('[Note: Translation service')) {
        hasShownTranslationNoteRef.current = true;
      }
      setIsTranslating(false);
    } else {
      // Otherwise, show English version
      setGeneratedText(englishNarrative);
      lastTranslatedLangRef.current = 'en';
      hasShownTranslationNoteRef.current = false;
    }
    
    setStep(3);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      // Simulate email extraction
      setExtractedEmails([
        "editor@thehindu.com",
        "news@economictimes.com",
        "media@timesgroup.com",
        "contact@mint.com",
      ]);
    }
  };

  const handleSendEmails = () => {
    // This would integrate with email service
    alert(`Sending to ${extractedEmails.length} contacts with subject: "${emailSubject}"`);
    setShowEmailModal(false);
  };

  return (
    <main className="min-h-screen pt-20 bg-black">
      <div className="container mx-auto px-6 py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-5xl md:text-6xl font-bold mb-4">Regional Narrative Engine</h1>
          <p className="text-xl text-gray-400 font-light">
            Transform one English press release into multiple culturally-nuanced regional narratives in under 30 seconds
          </p>
        </motion.div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-12">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-light transition-all ${
                  s <= step ? "bg-white text-black" : "bg-gray-800 text-gray-500"
                }`}
              >
                {s}
              </div>
              {s < 3 && (
                <div
                  className={`w-24 h-px mx-4 transition-all ${
                    s < step ? "bg-white" : "bg-gray-800"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Source Content Ingestion */}
        {step === 1 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="max-w-4xl mx-auto"
          >
            <div className="glass-effect p-8 rounded-lg mb-6">
              <h2 className="text-3xl font-bold mb-6">Step 1: Source Content</h2>

              {/* Auto-Summarize Toggle */}
              <div className="flex items-center gap-3 mb-6">
                <button
                  onClick={() => setAutoSummarize(!autoSummarize)}
                  className={`px-6 py-2 rounded-sm font-light transition-all ${
                    autoSummarize ? "bg-white text-black" : "bg-gray-800 text-white"
                  }`}
                >
                  <Sparkles className="w-4 h-4 inline mr-2" />
                  Auto-Summarize
                </button>
                {autoSummarize && (
                  <span className="text-sm text-gray-400">
                    AI will generate a 3-paragraph executive summary
                  </span>
                )}
              </div>

              {/* Source Text Input */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-2 font-light">
                  Source Text (English)
                </label>
                <textarea
                  value={sourceText}
                  onChange={(e) => setSourceText(e.target.value)}
                  placeholder="Paste your press release, drag & drop a file, or insert a link..."
                  className="w-full h-64 bg-black border border-gray-700 rounded p-4 text-white font-light focus:border-white focus:outline-none transition-colors resize-none"
                />
                <div className="flex gap-4 mt-4">
                  <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded hover:bg-gray-700 transition-colors">
                    <Upload className="w-4 h-4" />
                    <span className="text-sm font-light">Upload File</span>
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded hover:bg-gray-700 transition-colors">
                    <FileText className="w-4 h-4" />
                    <span className="text-sm font-light">From Link</span>
                  </button>
                </div>
              </div>


              <button
                onClick={() => setStep(2)}
                disabled={!sourceText}
                className="w-full py-4 bg-white text-black font-medium rounded-sm hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next: Contextual Targeting
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 2: Contextual Targeting & Control */}
        {step === 2 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="max-w-4xl mx-auto"
          >
            <div className="glass-effect p-8 rounded-lg mb-6">
              <h2 className="text-3xl font-bold mb-6">Step 2: Contextual Targeting</h2>

              {/* Tonal Presets */}
              <div className="mb-8">
                <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5" />
                  Select Target Region
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {regions.map((region) => (
                    <button
                      key={region.name}
                      onClick={() => handleRegionChange(region.name)}
                      className={`px-4 py-3 rounded-md border flex flex-col items-center ${
                        selectedRegion === region.name
                          ? "border-blue-500 bg-blue-500/10 text-blue-500"
                          : "border-gray-700 hover:border-gray-600"
                      } transition-colors`}
                    >
                      <span>{region.name}</span>
                      <span className="text-xs text-gray-400 mt-1">
                        {region.languages.length} languages
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="mb-8">
                <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                  <Languages className="w-5 h-5" />
                  Select Language
                </h3>
                {!selectedRegion ? (
                  <div className="text-gray-400 text-sm py-4">
                    Please select a region first to see available languages
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {availableLanguages.map((language) => (
                      <button
                        key={language.code}
                        onClick={() => setSelectedLanguage(language.code)}
                        className={`px-4 py-2 rounded-md border flex items-center justify-center gap-2 ${
                          selectedLanguage === language.code
                            ? "border-blue-500 bg-blue-500/10 text-blue-500"
                            : "border-gray-700 hover:border-gray-600"
                        } transition-colors`}
                      >
                        {language.name}
                        {isTranslating && selectedLanguage === language.code && (
                          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
                
                {/* Translation progress bar */}
                {isTranslating && (
                  <div className="mt-4">
                    <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${translationProgress}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-400 mt-1 text-right">
                      Translating content...
                    </div>
                  </div>
                )}
              </div>

              {/* Media Type */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-2 font-light">Media Type</label>
                <select
                  value={selectedMediaType}
                  onChange={(e) => setSelectedMediaType(e.target.value)}
                  className="w-full bg-black border border-gray-700 rounded p-3 text-white font-light focus:border-white focus:outline-none"
                >
                  <option value="">Select Type</option>
                  {mediaTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              {/* Tonal Presets */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-3 font-light">Tone</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {tonePresets.map((preset) => (
                    <button
                      key={preset.value}
                      onClick={() => setTonePreset(preset.value)}
                      className={`py-3 px-4 rounded-sm font-light transition-all ${
                        tonePreset === preset.value
                          ? "bg-white text-black"
                          : "bg-gray-800 text-white hover:bg-gray-700"
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Word Count */}
              <div className="mb-8">
                <label className="block text-sm text-gray-400 mb-3 font-light">
                  Target Word Count: {wordCount} words (excluding spaces)
                </label>
                <div className="flex gap-4 items-center">
                  <input
                    type="range"
                    min="100"
                    max="1000"
                    step="50"
                    value={wordCount}
                    onChange={(e) => setWordCount(parseInt(e.target.value))}
                    className="flex-1"
                  />
                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => setWordCount(100)}
                      className="px-3 py-1.5 text-xs bg-gray-800 rounded hover:bg-gray-700"
                    >
                      Short (100)
                    </button>
                    <button
                      onClick={() => setWordCount(250)}
                      className="px-3 py-1.5 text-xs bg-gray-800 rounded hover:bg-gray-700"
                    >
                      Medium (250)
                    </button>
                    <button
                      onClick={() => setWordCount(500)}
                      className="px-3 py-1.5 text-xs bg-gray-800 rounded hover:bg-gray-700"
                    >
                      Long (500)
                    </button>
                    <button
                      onClick={() => setWordCount(750)}
                      className="px-3 py-1.5 text-xs bg-gray-800 rounded hover:bg-gray-700"
                    >
                      Extended (750)
                    </button>
                    <button
                      onClick={() => setWordCount(1000)}
                      className="px-3 py-1.5 text-xs bg-gray-800 rounded hover:bg-gray-700"
                    >
                      Comprehensive (1000)
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 py-4 border border-white text-white font-light rounded-sm hover:bg-white hover:text-black transition-all"
                >
                  Back
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={!selectedRegion || !selectedMediaType}
                  className="flex-1 py-4 bg-white text-black font-medium rounded-sm hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-5 h-5" />
                  Generate Narrative
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Step 3: Generation & Review */}
        {step === 3 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="max-w-6xl mx-auto"
          >
            <div className="glass-effect p-8 rounded-lg">
              <h2 className="text-3xl font-bold mb-6">Step 3: Review & Refine</h2>

              {/* Side-by-Side Comparison */}
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                {/* Source */}
                <div>
                  <h3 className="text-sm text-gray-400 mb-3 font-light">Source Text (English)</h3>
                  <div className="bg-black border border-gray-700 rounded p-4 h-80 overflow-y-auto">
                    <p className="text-white font-light whitespace-pre-wrap">{sourceText}</p>
                  </div>
                </div>

                {/* Generated */}
                <div>
                  <h3 className="text-sm text-gray-400 mb-3 font-light">
                    Generated ({selectedLanguage} - {selectedMediaType})
                  </h3>
                  <div className="bg-black border border-green-600 rounded p-4 h-80 overflow-y-auto">
                    <p className="text-white font-light whitespace-pre-wrap">{generatedText}</p>
                  </div>
                </div>
              </div>

              {/* Refine Prompt */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-2 font-light">
                  Refine this result (optional)
                </label>
                <div className="flex gap-3">
                  <input
                    type="text"
                    placeholder="e.g., 'Make the opening paragraph more aggressive' or 'Use simpler language'"
                    className="flex-1 bg-black border border-gray-700 rounded p-3 text-white font-light focus:border-white focus:outline-none"
                  />
                  <button className="px-6 py-3 bg-gray-800 rounded hover:bg-gray-700 transition-colors">
                    <RefreshCw className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4">
                <button
                  onClick={() => setStep(2)}
                  className="px-8 py-4 border border-white text-white font-light rounded-sm hover:bg-white hover:text-black transition-all"
                >
                  Modify Parameters
                </button>
                <button
                  onClick={handleCopy}
                  className="flex-1 py-4 bg-gray-800 text-white font-light rounded-sm hover:bg-gray-700 transition-all flex items-center justify-center gap-2"
                >
                  {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                  {copied ? "Copied!" : "Copy to Clipboard"}
                </button>
                <button 
                  onClick={() => setShowEmailModal(true)}
                  className="flex-1 py-4 bg-blue-600 text-white font-medium rounded-sm hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
                >
                  <Mail className="w-5 h-5" />
                  Apply to Contacts
                </button>
                <button className="flex-1 py-4 bg-white text-black font-medium rounded-sm hover:bg-gray-200 transition-all flex items-center justify-center gap-2">
                  <Send className="w-5 h-5" />
                  Pitch Ready
                </button>
              </div>

              {/* Feedback Loop */}
              <div className="mt-6 pt-6 border-t border-gray-800">
                <p className="text-sm text-gray-400 mb-3 font-light">
                  Did you need to make manual edits?
                </p>
                <div className="flex gap-3">
                  {["Tone was wrong", "Language inaccurate", "Wrong terminology", "Cultural context missed"].map((feedback) => (
                    <button
                      key={feedback}
                      className="px-4 py-2 bg-gray-900 border border-gray-700 rounded-sm text-sm font-light hover:border-gray-500 transition-colors"
                    >
                      {feedback}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Email Modal */}
        {showEmailModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-6">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-effect p-8 rounded-lg max-w-2xl w-full"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold">Apply to Contacts</h2>
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="text-gray-400 hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>

              {/* Upload Section */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-3 font-light">
                  Upload Contact List (Excel/Google Sheets)
                </label>
                <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center hover:border-gray-500 transition-colors">
                  <input
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer flex flex-col items-center gap-3"
                  >
                    <Upload className="w-12 h-12 text-gray-400" />
                    <div>
                      <p className="text-white font-light mb-1">
                        {uploadedFile ? uploadedFile.name : "Click to upload or drag and drop"}
                      </p>
                      <p className="text-sm text-gray-500 font-light">
                        Excel (.xlsx, .xls) or CSV files
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              {/* Extracted Emails */}
              {extractedEmails.length > 0 && (
                <div className="mb-6">
                  <label className="block text-sm text-gray-400 mb-3 font-light flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    Extracted Email Addresses ({extractedEmails.length})
                  </label>
                  <div className="bg-black border border-gray-700 rounded p-4 max-h-40 overflow-y-auto">
                    {extractedEmails.map((email, i) => (
                      <div key={i} className="text-sm text-gray-300 font-light py-1">
                        {email}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Email Subject */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-2 font-light">
                  Email Subject *
                </label>
                <input
                  type="text"
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                  placeholder="e.g., Exclusive: New Product Launch in Regional Markets"
                  className="w-full bg-black border border-gray-700 rounded p-3 text-white font-light focus:border-white focus:outline-none"
                />
              </div>

              {/* Email Preview */}
              <div className="mb-6">
                <label className="block text-sm text-gray-400 mb-2 font-light">
                  Email Body Preview
                </label>
                <div className="bg-black border border-gray-700 rounded p-4 max-h-60 overflow-y-auto">
                  <p className="text-white font-light text-sm whitespace-pre-wrap">
                    {generatedText || "Your generated narrative will appear here..."}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4">
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="flex-1 py-3 border border-white text-white font-light rounded-sm hover:bg-white hover:text-black transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendEmails}
                  disabled={!emailSubject || extractedEmails.length === 0}
                  className="flex-1 py-3 bg-white text-black font-medium rounded-sm hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Send className="w-5 h-5" />
                  Send to {extractedEmails.length} Contacts
                </button>
              </div>

              <p className="text-xs text-gray-500 text-center mt-4 font-light">
                Emails will be sent via your connected email service (Gmail, Outlook, SendGrid)
              </p>
            </motion.div>
          </div>
        )}
      </div>
    </main>
  );
}
