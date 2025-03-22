//This is where I'll connect Firebase

// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import { collection, getFirestore } from 'firebase/firestore';

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseApp initializeApp = ({
  apiKey: "AIzaSyCOaOWgmWZACwroiwMk8PgZ3FkouTFf7zs",
  authDomain: "nextgenmarketplace-3c041.firebaseapp.com",
  projectId: "nextgenmarketplace-3c041",
  storageBucket: "nextgenmarketplace-3c041.firebasestorage.app",
  messagingSenderId: "647637034752",
  appId: "1:647637034752:web:d188f7820264ad6a10b5e5",
  measurementId: "G-XKD3BYRLJM"
});

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const db = getFirestore(app);
const auth = getAuth(app)
const todosCol = collection(db, 'todos')


//detect auth 
onAuthStateChanged(auth, user => {
    if (user != null){
        console.log('logged in!');
    } else {
        console.log('no user')
    }
});


