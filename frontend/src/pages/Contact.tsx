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

const Contact: React.FC = () => {
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
            <header className="p-6">
                <div className="flex items-center">
                    <img
                        src={isDarkMode ? whiteLogo : darkLogo}
                        alt="True Vision Logo"
                        className="h-[90px] w-auto"
                    />
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-grow flex items-center justify-center p-6">
                <div className="container flex flex-col items-center max-w-6xl mx-auto gap-12">
                    {/* Team Members Row */}
                    <div className="w-full flex flex-row flex-wrap justify-center gap-8">
                        {teamMembers.map((member, index) => (
                            <div key={index} className={`${isDarkMode ? 'bg-neutral-900' : 'bg-white'} rounded-lg p-8 shadow-lg flex flex-col items-center flex-1 min-w-[260px]`}>
                                <div className="rounded-lg overflow-hidden bg-black w-full max-w-[320px] aspect-square flex items-center justify-center mb-6">
                                    <img
                                        src={member.image}
                                        alt={member.name}
                                        className="w-full h-auto object-cover aspect-square"
                                    />
                                </div>
                                <h3 className={`text-lg font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>{member.name}</h3>
                                <a
                                    href={member.linkedin}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 text-[#097F4D] hover:text-[#076b41] transition-colors text-sm"
                                >
                                    <FaLinkedin className="text-lg" />
                                    <span>LinkedIn</span>
                                </a>
                            </div>
                        ))}
                    </div>
                    {/* Page Title and Description */}
                    <div className="w-full text-center flex flex-col gap-6 mt-8">
                        <h1 className="text-6xl md:text-7xl font-bold">
                            <span className={isDarkMode ? "text-white" : "text-gray-800"}>Contact</span>{' '}
                            <span className="text-[#097F4D]">Us</span>
                        </h1>

                        <p className={`${isDarkMode ? "text-gray-400" : "text-gray-600"} text-lg`}>
                            Get to know the talented individuals behind True Vision. Connect with us for any inquiries or collaborations!
                        </p>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="p-6">
                <div className="flex justify-center gap-4 text-base">
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