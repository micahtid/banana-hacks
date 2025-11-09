/**
 * UserProvider
 * 
 * Provides Firebase authentication state throughout the application
 * Manages user login/logout state with real-time updates
 */

"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { User } from "firebase/auth";

import { initializeFirebase, getUserAuth } from "@/utils/database_functions";

/* ============================================
   TYPES
   ============================================ */

// Context type definition
type UserContextType = {
  user: User | null | undefined;  // undefined = loading, null = logged out, User = logged in
};

export interface Props {
  [key: string]: any;
}

/* ============================================
   CONTEXT CREATION
   ============================================ */

// Create user context
export const UserContext = createContext<UserContextType | undefined>(
  undefined
);

/* ============================================
   PROVIDER COMPONENT
   ============================================ */

export const UserContextProvider = ({ children, ...props }: Props) => {
  // Initialize Firebase
  const app = initializeFirebase();
  const auth = getUserAuth(true);
  
  // User state: undefined (loading), null (logged out), User (logged in)
  const [user, setUser] = useState<User | null | undefined>(undefined);

  // Subscribe to auth state changes
  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((firebaseUser) => {
      if (firebaseUser) {
        // User is signed in
        setUser(firebaseUser);
      } else {
        // User is signed out
        setUser(null);
      }
    });
    
    // Cleanup subscription on unmount
    return () => unsubscribe();
  }, [auth]);

  return (
    <UserContext.Provider value={{ user }} {...props}>
      {children}
    </UserContext.Provider>
  );
};

/* ============================================
   HOOKS
   ============================================ */

/**
 * Hook for accessing user context
 * @throws Error if used outside of UserContextProvider
 */
export const useUser = () => {
  const context = useContext(UserContext);
  if (!context)
    throw new Error("useUser must be used within a UserContextProvider");
  return context;
};