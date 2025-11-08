import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithRedirect, signInWithPopup } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// initializing firebase: auth and login
// sign in and sign out functions

export const initializeFirebase = () => {
  const firebaseConfig = {
    apiKey: "AIzaSyBcUuGzuZtK4IMpA34Mn7rO4yREJOoyA3A",
    authDomain: "corn-hacks.firebaseapp.com",
    projectId: "corn-hacks",
    storageBucket: "corn-hacks.firebasestorage.app",
    messagingSenderId: "837856312087",
    appId: "1:837856312087:web:b8758c25758e0f9a671552",
    measurementId: "G-B7QWF5JHVL"
  };

  const app = initializeApp(firebaseConfig);
  return app;
}

export const getUserAuth = (alreadyInit: boolean) => {
  if (!alreadyInit) {
    const app = initializeFirebase();
  }
  const auth = getAuth();
  return auth;
}

export const getFireStore = (alreadyInit: boolean) => {
  if (!alreadyInit) {
    const app = initializeFirebase();
  }
  const firestore = getFirestore();
  return firestore;
}

export const signIn = () => {
  const auth = getUserAuth(false);
  const provider = new GoogleAuthProvider();
//   signInWithRedirect(auth, provider);
  signInWithPopup(auth, provider);
}

export const signOut = () => {
  const auth = getUserAuth(false);
  auth.signOut();
}