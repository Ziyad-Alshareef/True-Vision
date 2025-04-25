import { type ClassValue, clsx } from "clsx";
import * as twMergeModule from "tailwind-merge";

// Fallback implementation if libraries aren't available
function fallbackCn(...inputs: string[]) {
  return inputs.filter(Boolean).join(' ');
}

export function cn(...inputs: ClassValue[]) {
  try {
    // Try to use the libraries if available
    return twMergeModule.twMerge(clsx(inputs));
  } catch (error) {
    // Fallback to simple string concatenation if libraries aren't available
    console.warn('Error using twMerge or clsx:', error);
    return fallbackCn(...inputs.map(i => String(i)));
  }
}
