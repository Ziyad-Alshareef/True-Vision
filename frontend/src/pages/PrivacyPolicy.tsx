import React from 'react';
import { Link } from 'react-router-dom';
import whiteLogo from "./assets/whitefont-transpa.png";
import darkLogo from "./assets/output-onlinepngtoolsblack font transpa.png";
import { GreenCircle } from '../components/GreenCircle';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';

const PrivacyPolicy: React.FC = () => {
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
                <div className="container max-w-4xl mx-auto">
                    <div className={`${isDarkMode ? 'bg-neutral-900' : 'bg-white'} rounded-lg p-8 shadow-lg`}>
                        <h1 className={`text-4xl font-bold mb-8 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
                            Privacy Policy
                        </h1>

                        <div className={`space-y-6 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                            <section>
                                <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
                                <p>
                                    At True Vision, we are committed to protecting your privacy and ensuring the security of your personal information. This Privacy Policy explains how we collect, use, and safeguard your data when you use our deepfake detection services.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">2. Information We Collect</h2>
                                <ul className="list-disc pl-6 space-y-2">
                                    <li>Video files uploaded for deepfake detection</li>
                                    <li>Account information (if you create an account)</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Information</h2>
                                <ul className="list-disc pl-6 space-y-2">
                                    <li>To provide and improve our deepfake detection services</li>
                                    <li>To analyze and enhance our algorithms</li>
                                    <li>To communicate with you about our services</li>
                                    <li>To make improvements to our services</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">4. Data Security</h2>
                                <p>
                                    We implement appropriate technical and organizational measures to protect your data against unauthorized access, alteration, disclosure, or destruction.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">5. Your Rights</h2>
                                <ul className="list-disc pl-6 space-y-2">
                                    <li>Right to access your personal data</li>
                                    <li>Right to request deletion of your data</li>
                                    <li>Right to be notified of any data breaches</li>
                                    <li>Right to be notified of any changes to this policy</li>
                                </ul>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">6. Contact Us</h2>
                                <p>
                                    If you have any questions about this Privacy Policy or our data practices, please contact us through our Contact page.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-2xl font-semibold mb-4">7. Updates to This Policy</h2>
                                <p>
                                    We may update this Privacy Policy from time to time.
                                </p>
                            </section>
                        </div>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="p-4">
                <div className="flex justify-center gap-4 text-sm">
                    <Link to="/" className="text-[#097F4D] hover:text-[#076b41]">
                        Home
                    </Link>
                    <span className="text-[#097F4D]">|</span>
                    <Link to="/contact" className="text-[#097F4D] hover:text-[#076b41]">
                        Contact Us
                    </Link>
                </div>
            </footer>
        </div>
    );
};

export default PrivacyPolicy; 