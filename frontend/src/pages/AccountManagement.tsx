import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';
import { GreenCircle } from '../components/GreenCircle';
import whiteLogo from "./assets/whitefont-transpa.png";
import darkLogo from "./assets/output-onlinepngtoolsblack font transpa.png";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "../components/ui/dialog";

interface ValidationError {
    field: string;
    message: string;
}

interface UserData {
    email: string;
    username: string;
}

export const AccountManagement = () => {
    const navigate = useNavigate();
    const { isDarkMode, isTransitioning } = useTheme();
    const [username, setUsername] = useState('User'); // TODO: Replace with actual user data
    const [email, setEmail] = useState('user@example.com'); // TODO: Replace with actual user data
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [errors, setErrors] = useState<ValidationError[]>([]);
    const [message, setMessage] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [deletePassword, setDeletePassword] = useState('');

    const validateForm = (): boolean => {
        const newErrors: ValidationError[] = [];

        if (newPassword) {
            if (newPassword.length < 8) {
                newErrors.push({ field: 'newPassword', message: 'Password must be at least 8 characters long' });
            }
            if (!/[a-zA-Z]/.test(newPassword)) {
                newErrors.push({ field: 'newPassword', message: 'Password must contain at least 1 character' });
            }
        }

        if (newPassword && newPassword !== confirmPassword) {
            newErrors.push({ field: 'confirmPassword', message: 'Passwords do not match' });
        }

        if (newPassword && !currentPassword) {
            newErrors.push({ field: 'currentPassword', message: 'Current password is required to set a new password' });
        }

        setErrors(newErrors);
        return newErrors.length === 0;
    };

    const getErrorForField = (field: string): string | undefined => {
        return errors.find(error => error.field === field)?.message;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!validateForm()) return;

        setIsLoading(true);
        try {
            // TODO: Implement password update logic
            setMessage('Password updated successfully!');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (error) {
            console.error('Update error:', error);
            setMessage('Error updating password. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (!deletePassword) {
            setMessage('Please enter your password to confirm account deletion');
            return;
        }

        try {
            // TODO: Implement account deletion logic
            localStorage.removeItem('access');
            localStorage.removeItem('refresh');
            navigate('/');
        } catch (error) {
            setMessage('Error deleting account. Please try again.');
        }
    };

    return (
        <div className={`min-h-screen w-full ${isDarkMode ? 'bg-[#222222]' : 'bg-gray-50'} flex flex-col ${isTransitioning ? 'theme-transitioning' : ''}`}>
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

            {/* Main content with proper padding and scrolling */}
            <main className="flex-grow px-6 pb-6">
                <div className="max-w-2xl mx-auto">
                    <h1 className={`text-2xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'} mb-8`}>
                        Account Settings
                    </h1>

                    {message && (
                        <div className={`mb-6 p-3 rounded ${message.includes('successfully') ? 'bg-green-600' : 'bg-red-600'} text-white`}>
                            {message}
                        </div>
                    )}

                    <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-neutral-900' : 'bg-white'} shadow-lg`}>
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-4">
                                <div>
                                    <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                        Username
                                    </label>
                                    <Input
                                        type="text"
                                        value={username}
                                        disabled
                                        className={`${isDarkMode ? 'bg-neutral-800 border-neutral-700 text-gray-300' : 'bg-gray-100 border-gray-200 text-gray-700'}`}
                                    />
                                </div>

                                <div>
                                    <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                        Email
                                    </label>
                                    <Input
                                        type="email"
                                        value={email}
                                        disabled
                                        className={`${isDarkMode ? 'bg-neutral-800 border-neutral-700 text-gray-300' : 'bg-gray-100 border-gray-200 text-gray-700'}`}
                                    />
                                </div>
                            </div>

                            <div className="pt-6 border-t border-gray-700">
                                <h2 className={`text-lg font-medium mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                    Change Password
                                </h2>

                                <div className="space-y-4">
                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            Current Password
                                        </label>
                                        <Input
                                            type="password"
                                            value={currentPassword}
                                            onChange={(e) => setCurrentPassword(e.target.value)}
                                            className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'}`}
                                        />
                                        {getErrorForField('currentPassword') && (
                                            <p className="text-red-500 text-sm mt-1">{getErrorForField('currentPassword')}</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            New Password
                                        </label>
                                        <Input
                                            type="password"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'}`}
                                        />
                                        {getErrorForField('newPassword') && (
                                            <p className="text-red-500 text-sm mt-1">{getErrorForField('newPassword')}</p>
                                        )}
                                    </div>

                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            Confirm New Password
                                        </label>
                                        <Input
                                            type="password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'}`}
                                        />
                                        {getErrorForField('confirmPassword') && (
                                            <p className="text-red-500 text-sm mt-1">{getErrorForField('confirmPassword')}</p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4 pt-4 sm:pt-6 w-full">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => navigate('/dashboard')}
                                    className={`w-full ${isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-800' : ''}`}
                                >
                                    Back to Dashboard
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={isLoading}
                                    className={`w-full auth-button ${isDarkMode ? 'text-white' : ''}`}
                                >
                                    {isLoading ? 'Saving...' : 'Save Changes'}
                                </Button>
                            </div>
                        </form>
                    </div>

                    <div className="mt-8 pt-6 border-t border-gray-700">
                        <h2 className={`text-lg font-medium mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            Account Deletion
                        </h2>
                        <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-red-900/20' : 'bg-red-50'} border border-red-500/20`}>
                            <div className="flex flex-col space-y-3 sm:space-y-4">
                                <div>
                                    <h3 className={`text-base sm:text-lg font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                        Delete Account
                                    </h3>
                                    <p className={`mt-1 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                        Once you delete your account, there is no going back. Please be certain.
                                    </p>
                                </div>
                                <Button
                                    variant="destructive"
                                    onClick={() => setIsDeleteDialogOpen(true)}
                                    className="w-full sm:w-fit"
                                >
                                    Delete Account
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <DialogContent className={`${isDarkMode ? 'dark bg-neutral-900 text-white' : 'light bg-white text-gray-900'}`}>
                    <DialogHeader>
                        <DialogTitle className={isDarkMode ? 'text-white' : 'text-gray-900'}>Delete Account</DialogTitle>
                        <DialogDescription className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>
                            Are you sure you want to delete your account? This action cannot be undone. All your data will be permanently deleted.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                        <Input
                            type="password"
                            placeholder="Enter your password to confirm"
                            value={deletePassword}
                            onChange={(e) => setDeletePassword(e.target.value)}
                            className={`${isDarkMode ? 'bg-[#333333] border-none text-white' : 'bg-white border-gray-300 text-gray-800'}`}
                        />
                    </div>
                    <DialogFooter className="flex flex-col sm:flex-row justify-center gap-2 sm:gap-4 w-full">
                        <Button
                            variant={isDarkMode ? "outline" : "secondary"}
                            onClick={() => setIsDeleteDialogOpen(false)}
                            className="w-full"
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleDeleteAccount}
                            className="w-full"
                        >
                            Delete Account
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default AccountManagement; 