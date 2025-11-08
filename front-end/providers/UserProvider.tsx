"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { User } from "firebase/auth";

import { initializeFirebase, getUserAuth } from "@/utils/database_functions";

// context type definition
type UserContextType = {
  user: User | null | undefined;
};

// creating user context
export const UserContext = createContext<UserContextType | undefined>(
  undefined
);

export interface Props {
  [key: string]: any;
}

export const UserContextProvider = ({ children, ...props }: Props) => {
  const app = initializeFirebase();
  const auth = getUserAuth(true);
  
  const [user, setUser] = useState<User | null | undefined>(undefined);

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((firebaseUser) => {
      if (firebaseUser) {
        // update user states
        setUser(firebaseUser);
      } else {
        // update states during logout
        setUser(null);
      }
    });
    
    return () => unsubscribe();
  }, [auth]);

  return (
    <UserContext.Provider value={{ user }} {...props}>
      {children}
    </UserContext.Provider>
  );
};

// hook for accessing user context
export const useUser = () => {
  const context = useContext(UserContext);
  if (!context)
    throw new Error("useUser must be used within a UserContextProvider");
  return context;
};