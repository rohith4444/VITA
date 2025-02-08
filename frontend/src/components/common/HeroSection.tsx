import React from 'react';

const HeroSection = () => {
  return (
    <div className="min-h-screen bg-[#FAF7F5] p-8">
      {/* Navigation Bar */}
      <nav className="flex items-center justify-between mb-24">
        <div className="text-xl font-bold">ANTHROPIC</div>
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-1">
            Claude
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
              <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
          <span>Research</span>
          <span>Company</span>
          <span>Careers</span>
          <span>News</span>
          <button className="px-4 py-2 bg-black text-white rounded">Try Claude</button>
        </div>
      </nav>

      {/* Main Hero Content */}
      <div className="flex">
        <div className="w-2/3">
          <h1 className="text-6xl font-bold leading-tight mb-16">
            AI <span className="underline">research</span> and <span className="underline">products</span> that put safety at the frontier
          </h1>

          {/* Cards */}
          <div className="grid grid-cols-2 gap-8">
            {/* Claude Card */}
            <div className="bg-white p-8 rounded-xl">
              <div className="text-sm font-semibold mb-4">CLAUDE.AI</div>
              <h2 className="text-2xl font-bold mb-4">Meet Claude 3.5 Sonnet</h2>
              <p className="text-gray-700 mb-8">Claude 3.5 Sonnet, our most intelligent AI model, is now available.</p>
              <button className="w-full py-3 bg-black text-white rounded">Talk to Claude</button>
            </div>

            {/* API Card */}
            <div className="bg-white p-8 rounded-xl">
              <div className="text-sm font-semibold mb-4">API</div>
              <h2 className="text-2xl font-bold mb-4">Build with Claude</h2>
              <p className="text-gray-700 mb-8">Create AI-powered applications and custom experiences using Claude.</p>
              <button className="w-full py-3 border-2 border-black rounded">Learn more</button>
            </div>
          </div>
        </div>

        {/* Illustration */}
        <div className="w-1/3 flex justify-center items-start">
          <svg width="400" height="400" viewBox="0 0 400 400" fill="none">
            <circle cx="200" cy="200" r="100" fill="#E4B7A0"/>
            <path d="M200,100 Q300,200 200,300 Q100,200 200,100" fill="none" stroke="black" strokeWidth="3"/>
            <circle cx="150" cy="150" r="20" fill="#E4B7A0"/>
            <circle cx="250" cy="150" r="20" fill="#E4B7A0"/>
            <circle cx="200" cy="250" r="20" fill="#E4B7A0"/>
            <circle cx="150" cy="250" r="20" fill="#E4B7A0"/>
            <circle cx="250" cy="250" r="20" fill="#E4B7A0"/>
          </svg>
        </div>
      </div>
    </div>
  );
};

export default HeroSection;