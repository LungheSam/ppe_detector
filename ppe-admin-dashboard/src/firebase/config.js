import { initializeApp } from 'firebase/app';
import { getDatabase } from 'firebase/database';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  databaseURL: process.env.REACT_APP_FIREBASE_DATABASE_URL,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID
};

// Validate that all required config values are present
const requiredKeys = ['apiKey', 'authDomain', 'projectId', 'storageBucket', 'messagingSenderId', 'appId'];
const missingKeys = requiredKeys.filter(key => !firebaseConfig[key]);

if (missingKeys.length > 0) {
  console.error('❌ Missing Firebase configuration keys:', missingKeys);
  console.error('📝 Environment variables:', {
    apiKey: process.env.REACT_APP_FIREBASE_API_KEY ? '✓ Present' : '✗ Missing',
    authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN ? '✓ Present' : '✗ Missing',
    projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID ? '✓ Present' : '✗ Missing',
    storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET ? '✓ Present' : '✗ Missing',
    messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID ? '✓ Present' : '✗ Missing',
    appId: process.env.REACT_APP_FIREBASE_APP_ID ? '✓ Present' : '✗ Missing'
  });
} else {
  console.log('✅ Firebase configuration loaded successfully');
  console.log('📝 Project ID:', firebaseConfig.projectId);
}

const app = initializeApp(firebaseConfig);
export const database = getDatabase(app);
export const auth = getAuth(app);
export const firestore = getFirestore(app);
export default app;