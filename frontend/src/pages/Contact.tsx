import React from 'react';
import { Link } from 'react-router-dom';
import whiteLogo from "./assets/whitefont-transpa.png";
import darkLogo from "./assets/output-onlinepngtoolsblack font transpa.png";
import ziyadImage from "../membersprofiles/ziyad-icon.jpg";
import abdulazizImage from "../membersprofiles/abdulaziz-icon.png";
import aliImage from "../membersprofiles/ali-icon.jpg";
import ibrahimImage from "../membersprofiles/ibrahim-icon.jpg";
import { GreenCircle } from '../components/GreenCircle';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';
import { FaLinkedin } from 'react-icons/fa';

// Team member data
const teamMembers = [
    {
        name: "Ziyad Alshareef",
        image: ziyadImage,
        linkedin: "https://www.linkedin.com/in/ziyad-alshareef-3770352b6/",
    },
    {
        name: "Ali Alhoshan",
        image: aliImage,
        linkedin: "https://www.linkedin.com/in/ali-alhoshan-981498287/",
    },
    {
        name: "Abdulaziz Alkharjy",
        image: abdulazizImage,
        linkedin: "https://www.linkedin.com/in/abdulaziz--saad/",
    },
    {
        name: "Ibrahim Althunayyan",
        image: ibrahimImage,
        linkedin: "https://www.linkedin.com/in/ibrahim-althunayyan/",
    }
];

export const Contact = () => {
    const { isDarkMode, isTransitioning } = useTheme();

    return (
        <div className={`min-h-screen w-full ${isDarkMode ? 'bg-neutral-950' : 'bg-gray-50'} flex flex-col ${isTransitioning ? 'theme-transitioning' : ''}`}>
            {/* Theme Toggle Button - Fixed Position */}
            <div className="fixed top-6 right-6 z-50">
                <ThemeToggle />
            </div>

            <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2" style={{ zIndex: 0 }}>
                <GreenCircle />
            </div>

            {/* Header */}
            <header className="p-4">
                <div className="flex items-center">
                    <Link to="/">
                        <img
                            src={isDarkMode ? whiteLogo : darkLogo}
                            alt="True Vision Logo"
                            className="h-[70px] w-auto"
                        />
                    </Link>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 container mx-auto px-6">
                {/* Page Title */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl md:text-4xl font-bold mb-2">
                        <span className={isDarkMode ? "text-white" : "text-gray-800"}>Meet Our </span>
                        <span className="text-[#097F4D]">Team</span>
                    </h1>
                    <p className={`${isDarkMode ? "text-gray-400" : "text-gray-600"} text-base max-w-2xl mx-auto`}>
                        Get to know the talented individuals behind True Vision who are dedicated to making the digital world safer.
                    </p>
                </div>

                {/* Team Members Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {teamMembers.map((member, index) => (
                        <div key={index} className={`${isDarkMode ? 'bg-neutral-900' : 'bg-white'} rounded-lg p-4 shadow-lg transition-all hover:shadow-xl`}>
                            <div className="aspect-square mb-3 overflow-hidden rounded-lg">
                                <img
                                    src={member.image}
                                    alt={member.name}
                                    className="w-full h-full object-cover"
                                />
                            </div>
                            <h3 className={`text-lg font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
                                {member.name}
                            </h3>
                            <a
                                href={member.linkedin}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 text-[#097F4D] hover:text-[#076b41] transition-colors"
                            >
                                <FaLinkedin className="text-lg" />
                                <span>Connect on LinkedIn</span>
                            </a>
                        </div>
                    ))}
                </div>
            </main>

            {/* Footer */}
            <footer className="p-4">
                <div className="flex justify-center gap-4 text-sm">
                    <Link to="/privacy-policy" className="text-[#097F4D] hover:text-[#076b41]">
                        Privacy Policy
                    </Link>
                    <span className="text-[#097F4D]">|</span>
                    <Link to="/" className="text-[#097F4D] hover:text-[#076b41]">
                        Home
                    </Link>
                </div>
            </footer>
        </div>
    );
};

export default Contact; 