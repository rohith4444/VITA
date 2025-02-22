import React from "react";
import "./company.css";
// import Image from "next/image";
import { useState, useEffect } from "react"
import { Image } from "@mui/icons-material";
// import "./styles/modern-company-page.css"

const companyValues = [
  {
    title: "Innovation",
    description: "Pushing the boundaries of AI technology to create groundbreaking solutions.",
  },
  {
    title: "User-Centric",
    description: "Developing AI agents that truly understand and meet user needs.",
  },
  {
    title: "Ethical AI",
    description: "Committed to developing AI responsibly with transparency and fairness.",
  },
  {
    title: "Collaboration",
    description: "Fostering a culture of teamwork and open communication.",
  },
]

const founders = [
  {
    name: "Rohith",
    role: "Co-Founder & CEO",
    bio: "Visionary leader with extensive experience in AI and machine learning.",
    image: "/placeholder.svg?height=400&width=400",
  },
  {
    name: "Sandeep",
    role: "Co-Founder & CTO",
    bio: "Technical genius behind our AI agent's core algorithms and architecture.",
    image: "/placeholder.svg?height=400&width=400",
  },
]

export default function Company() {
  const [darkMode, setDarkMode] = useState(false)

  useEffect(() => {
    if (darkMode) {
      document.body.classList.add("dark-mode")
    } else {
      document.body.classList.remove("dark-mode")
    }
  }, [darkMode])

  return (
    <div className="page-container">
      <button className="dark-mode-toggle" onClick={() => setDarkMode(!darkMode)}>
        {darkMode ? "☀️" : "🌙"}
      </button>
      <div className="content-wrapper">
        <h1 className="page-title">Innovating AI Solutions</h1>

        <section className="section">
          <h2 className="section-title">Our Core Values</h2>
          <div className="values-grid">
            {companyValues.map((value, index) => (
              <div key={index} className="card" style={{ animationDelay: `${index * 0.1}s` }}>
                <div className="card-header">
                  <h3 className="card-title">{value.title}</h3>
                </div>
                <div className="card-content">
                  <p className="card-text">{value.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Meet Our Visionaries</h2>
          <div className="team-grid">
            {founders.map((founder, index) => (
              <div key={index} className="team-member" style={{ animationDelay: `${index * 0.1}s` }}>
                <Image
                  src={founder.image || "/placeholder.svg"}
                  alt={founder.name}
                  width={200}
                  height={200}
                  className="team-member-image"
                />
                <h3 className="team-member-name">{founder.name}</h3>
                <p className="team-member-role">{founder.role}</p>
                <p className="team-member-bio">{founder.bio}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

