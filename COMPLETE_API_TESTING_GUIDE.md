# 🌍 Jamii Spot - Complete API Testing Guide

## 📋 **Overview**

This comprehensive guide covers testing for **ALL features** of the Jamii Spot backend API - a travel discovery platform that connects people from the same home country when they visit another country.

## 🎯 **Core Features Covered**

✅ **Authentication & JWT Management**  
✅ **Profile Management with Travel Data**  
✅ **Friend Request System with Real-time Notifications**  
✅ **Community Management**  
✅ **Story Posts (24-hour expiring media)**  
✅ **End-to-End Encrypted Messaging**  
✅ **Travel Discovery & Countrymate Finding**  
✅ **Local Expert Identification**  
✅ **Travel Buddy Matching**  
✅ **Smart Compatibility Scoring**  
✅ **Emergency Network**  
✅ **WebSocket Real-time Notifications**  
✅ **Travel Status Management**  

---

## 🚀 **Setup Instructions**

### **1. Start the Server**
```bash
cd C:\Users\eliza.ELIZABETH\Downloads\jamii-spot-backend
python manage.py runserver 0.0.0.0:8000
```

### **2. Import Postman Collection**
- Open Postman
- Import `Complete_Jamii_Spot_API.postman_collection.json`
- The collection includes automated tests and variable management

### **3. Alternative Testing Tools**
```bash
# For command line testing
curl

# For WebSocket testing
npm install -g wscat

# Or use browser developer tools (F12 → Console)
```

---

## 👤 **1. AUTHENTICATION & USER MANAGEMENT**

### **Test 1.1: User Registration**

#### **Create Test Users**

**John (Kenyan Traveler):**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_traveler",
    "email": "john@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Kimani"
  }'
```

**Mary (Local Expert):**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mary_expert",
    "email": "mary@example.com",
    "password": "securepass123",
    "first_name": "Mary",
    "last_name": "Wanjiku"
  }'
```

**David (Travel Buddy):**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "david_visitor",
    "email": "david@example.com",
    "password": "securepass123",
    "first_name": "David",
    "last_name": "Otieno"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "username": "john_traveler",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Kimani"
}
```

### **Test 1.2: JWT Authentication**

#### **Get JWT Tokens**
```bash
# John's token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_traveler",
    "password": "securepass123"
  }'

# Mary's token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "mary_expert",
    "password": "securepass123"
  }'

# David's token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "david_visitor",
    "password": "securepass123"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

⚠️ **Save the `access` tokens - you'll need them for all subsequent requests!**

### **Test 1.3: Token Refresh**
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

---

## 👤 **2. PROFILE MANAGEMENT**

### **Test 2.1: Setup Travel Profiles**

#### **John's Profile (Traveler)**
```bash
curl -X PATCH http://localhost:8000/api/profiles/1/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Software developer from Nairobi, exploring London for the first time!",
    "home_country": "Kenya",
    "home_city": "Nairobi",
    "current_country": "United Kingdom",
    "current_city": "London",
    "travel_status": "traveling",
    "travel_start_date": "2025-01-10",
    "travel_end_date": "2025-02-10",
    "is_available_to_help": true,
    "languages_spoken": ["English", "Swahili", "Kikuyu"],
    "years_in_current_location": null,
    "is_local_expert": false,
    "expertise_areas": []
  }'
```

#### **Mary's Profile (Local Expert)**
```bash
curl -X PATCH http://localhost:8000/api/profiles/2/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Kenyan living in London for 3 years. Happy to help fellow Kenyans!",
    "home_country": "Kenya",
    "home_city": "Mombasa",
    "current_country": "United Kingdom",
    "current_city": "London",
    "travel_status": "expat",
    "travel_start_date": null,
    "travel_end_date": null,
    "is_available_to_help": true,
    "languages_spoken": ["English", "Swahili", "Arabic"],
    "years_in_current_location": 3,
    "is_local_expert": true,
    "expertise_areas": ["transportation", "food", "accommodation", "culture", "shopping"]
  }'
```

#### **David's Profile (Travel Buddy)**
```bash
curl -X PATCH http://localhost:8000/api/profiles/3/ \
  -H "Authorization: Bearer YOUR_DAVID_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "University student visiting London during winter break",
    "home_country": "Kenya",
    "home_city": "Kisumu",
    "current_country": "United Kingdom",
    "current_city": "London",
    "travel_status": "traveling",
    "travel_start_date": "2025-01-05",
    "travel_end_date": "2025-01-25",
    "is_available_to_help": true,
    "languages_spoken": ["English", "Swahili", "Luo"],
    "years_in_current_location": null,
    "is_local_expert": false,
    "expertise_areas": []
  }'
```

### **Test 2.2: Get Profiles**

#### **Get All Profiles**
```bash
curl -X GET http://localhost:8000/api/profiles/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### **Get Specific Profile**
```bash
curl -X GET http://localhost:8000/api/profiles/2/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🤝 **3. FRIEND REQUEST SYSTEM**

### **Test 3.1: Send Friend Requests**

#### **John Sends Request to Mary**
```bash
curl -X POST http://localhost:8000/api/friend-requests/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_user": 2
  }'
```

🔔 **This triggers a real-time notification to Mary!**

### **Test 3.2: View Friend Requests**

#### **Mary's Received Requests**
```bash
curl -X GET http://localhost:8000/api/friend-requests/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "from_user": "john_traveler",
    "to_user": 2,
    "status": "pending",
    "created_at": "2025-01-12T10:30:00Z"
  }
]
```

### **Test 3.3: Accept Friend Request**

#### **Mary Accepts John's Request**
```bash
curl -X POST http://localhost:8000/api/friend-requests/1/accept/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN"
```

🔔 **This triggers an acceptance notification to John!**

**Expected Response:**
```json
{
  "status": "Friend request accepted.",
  "friend_request_id": 1,
  "new_friend": {
    "id": 1,
    "username": "john_traveler",
    "avatar": null
  }
}
```

### **Test 3.4: Reject Friend Request**
```bash
curl -X POST http://localhost:8000/api/friend-requests/1/reject/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN"
```

---

## 🏘️ **4. COMMUNITY MANAGEMENT**

### **Test 4.1: Create Community**

#### **Mary Creates Kenyan Community**
```bash
curl -X POST http://localhost:8000/api/communities/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kenyans in London",
    "description": "A community for Kenyans living in or visiting London. Share experiences, ask for help, and connect with fellow countrymates!",
    "is_channel": false
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "name": "Kenyans in London",
  "profile_image": null,
  "description": "A community for Kenyans living in or visiting London...",
  "created_by": "mary_expert",
  "created_at": "2025-01-12T10:45:00Z",
  "is_channel": false,
  "member_count": 1
}
```

### **Test 4.2: Get Communities**
```bash
curl -X GET http://localhost:8000/api/communities/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### **Test 4.3: Get Specific Community**
```bash
curl -X GET http://localhost:8000/api/communities/1/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📱 **5. STORY POSTS (24-HOUR EXPIRING MEDIA)**

### **Test 5.1: Get Stories**
```bash
curl -X GET http://localhost:8000/api/stories/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### **Test 5.2: Create Story Post**

#### **With Image Upload (using form-data)**
```bash
curl -X POST http://localhost:8000/api/stories/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -F "media_type=image" \
  -F "media_file=@/path/to/test/image.jpg"
```

#### **With Video Upload and Trimming**
```bash
curl -X POST http://localhost:8000/api/stories/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -F "media_type=video" \
  -F "media_file=@/path/to/test/video.mp4" \
  -F "start_time=5.0" \
  -F "end_time=20.0"
```

**Expected Response (202 Accepted):**
```json
{
  "id": 1,
  "sender": "john_traveler",
  "created_at": "2025-01-12T11:00:00Z",
  "items": [
    {
      "id": 1,
      "media_file": "/media/story_media/image.jpg",
      "media_type": "image",
      "duration_seconds": "5.00",
      "status": "processing"
    }
  ],
  "viewers": []
}
```

🔔 **This triggers:**
- Processing notification to story creator
- Friend notifications when processing completes

### **Test 5.3: Get Specific Story**
```bash
curl -X GET http://localhost:8000/api/stories/1/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔐 **6. ENCRYPTION & SECURITY**

### **Test 6.1: Generate Encryption Keys**

#### **Generate Keys for John**
```bash
curl -X POST http://localhost:8000/api/encryption-keys/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response (201 Created):**
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0B...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG...",
  "message": "IMPORTANT: Save the private key securely. It will not be shown again!"
}
```

⚠️ **CRITICAL**: Save the private key! It's shown only once.

#### **Generate Keys for Other Users**
```bash
# Mary
curl -X POST http://localhost:8000/api/encryption-keys/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# David
curl -X POST http://localhost:8000/api/encryption-keys/ \
  -H "Authorization: Bearer YOUR_DAVID_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### **Test 6.2: Get Public Keys**
```bash
curl -X GET http://localhost:8000/api/public-keys/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
[
  {
    "user": "john_traveler",
    "public_key": "-----BEGIN PUBLIC KEY-----\n...",
    "created_at": "2025-01-12T11:15:00Z"
  },
  {
    "user": "mary_expert",
    "public_key": "-----BEGIN PUBLIC KEY-----\n...",
    "created_at": "2025-01-12T11:16:00Z"
  }
]
```

---

## 💬 **7. MESSAGING SYSTEM WITH E2E ENCRYPTION**

### **Test 7.1: Create Conversations**

#### **Private Conversation**
```bash
curl -X POST http://localhost:8000/api/conversations/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_type": "private",
    "participant_ids": [2]
  }'
```

#### **Group Conversation**
```bash
curl -X POST http://localhost:8000/api/conversations/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_type": "group",
    "name": "London Travel Group",
    "description": "Kenyan travelers in London sharing tips and experiences",
    "participant_ids": [2, 3]
  }'
```

#### **Community Conversation (Auto-created with Community)**
Community conversations are automatically created when a community is created.

### **Test 7.2: Send Messages**

#### **Text Message**
```bash
curl -X POST http://localhost:8000/api/messages/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": 1,
    "message_type": "text",
    "content": "Hey Mary! I just arrived in London and would love some local tips!"
  }'
```

🔔 **This triggers a real-time message notification to Mary!**

#### **Reply to Message**
```bash
curl -X POST http://localhost:8000/api/messages/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": 1,
    "message_type": "text",
    "content": "Welcome to London, John! I'd be happy to help. The Tube is the best way to get around - get an Oyster card!",
    "reply_to": 1
  }'
```

#### **Media Message**
```bash
curl -X POST http://localhost:8000/api/messages/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -F "conversation=1" \
  -F "message_type=image" \
  -F "media_file=@/path/to/image.jpg"
```

### **Test 7.3: Get Messages**

#### **All Conversations**
```bash
curl -X GET http://localhost:8000/api/conversations/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### **Messages in Conversation**
```bash
curl -X GET "http://localhost:8000/api/messages/?conversation=1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "conversation": 1,
    "sender": {
      "id": 1,
      "username": "john_traveler",
      "first_name": "John",
      "last_name": "Kimani"
    },
    "message_type": "text",
    "encrypted_content": "{\"ciphertext\":\"...\",\"iv\":\"...\",\"tag\":\"...\"}",
    "timestamp": "2025-01-12T12:00:00Z",
    "reply_to": null,
    "reply_to_message": null,
    "is_read": false,
    "read_count": 0
  }
]
```

### **Test 7.4: Add Participants to Group**
```bash
curl -X POST http://localhost:8000/api/conversations/2/add_participants/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [4, 5]
  }'
```

---

## 🔍 **8. CORE DISCOVERY FEATURES**

### **Test 8.1: Find Countrymates Nearby (CORE FEATURE)**

#### **John Discovers Fellow Kenyans**
```bash
curl -X GET http://localhost:8000/api/discover/countrymates-nearby/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "message": "Found 2 people from Kenya in London",
  "location": {
    "home_country": "Kenya",
    "current_location": "London, United Kingdom"
  },
  "statistics": {
    "total_countrymates": 2,
    "travelers": 1,
    "residents": 0,
    "expats": 1,
    "local_experts": 1,
    "available_helpers": 2
  },
  "countrymates": [
    {
      "user": {
        "id": 2,
        "username": "mary_expert",
        "first_name": "Mary",
        "last_name": "Wanjiku"
      },
      "home_country": "Kenya",
      "current_city": "London",
      "travel_status": "expat",
      "travel_status_display": "Living Abroad Long-term",
      "is_traveling": false,
      "is_available_to_help": true,
      "is_local_expert": true,
      "expertise_areas": ["transportation", "food", "accommodation", "culture", "shopping"],
      "languages_spoken": ["English", "Swahili", "Arabic"],
      "years_in_current_location": 3,
      "helper_rating": "0.00",
      "days_in_current_location": 1095
    },
    {
      "user": {
        "id": 3,
        "username": "david_visitor",
        "first_name": "David",
        "last_name": "Otieno"
      },
      "home_country": "Kenya",
      "current_city": "London",
      "travel_status": "traveling",
      "is_traveling": true,
      "travel_start_date": "2025-01-05",
      "travel_end_date": "2025-01-25"
    }
  ]
}
```

🔔 **This triggers a discovery activity notification to John!**

### **Test 8.2: Find Local Experts**

```bash
curl -X GET http://localhost:8000/api/discover/local-experts/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "message": "Found 1 local experts in London",
  "location": "London, United Kingdom",
  "experts": [
    {
      "user": {
        "id": 2,
        "username": "mary_expert",
        "first_name": "Mary",
        "last_name": "Wanjiku"
      },
      "home_country": "Kenya",
      "current_city": "London",
      "is_local_expert": true,
      "expertise_areas": ["transportation", "food", "accommodation", "culture", "shopping"],
      "helper_rating": "0.00",
      "help_requests_fulfilled": 0,
      "years_in_current_location": 3,
      "is_available_to_help": true
    }
  ]
}
```

### **Test 8.3: Find Travel Buddies**

#### **John Looks for Travel Buddies**
```bash
curl -X GET http://localhost:8000/api/discover/travel-buddies/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "message": "Found 1 potential travel buddies",
  "your_travel_dates": {
    "start": "2025-01-10",
    "end": "2025-02-10"
  },
  "travel_buddies": [
    {
      "user": {
        "id": 3,
        "username": "david_visitor",
        "first_name": "David",
        "last_name": "Otieno"
      },
      "home_country": "Kenya",
      "travel_status": "traveling",
      "travel_start_date": "2025-01-05",
      "travel_end_date": "2025-01-25",
      "is_available_to_help": true
    }
  ]
}
```

#### **Mary (Non-Traveler) Tries to Find Travel Buddies**
```bash
curl -X GET http://localhost:8000/api/discover/travel-buddies/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "message": "You need to set your travel status to \"traveling\" to find travel buddies",
  "travel_status": "expat",
  "travel_buddies": []
}
```

### **Test 8.4: Smart Matches with Compatibility Scoring**

```bash
curl -X GET "http://localhost:8000/api/discover/smart-matches/?limit=10" \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "message": "Found 2 smart matches for you",
  "matching_criteria": {
    "home_country": "Kenya",
    "current_location": "London, United Kingdom",
    "travel_status": "traveling"
  },
  "matches": [
    {
      "user": {
        "id": 2,
        "username": "mary_expert"
      },
      "compatibility_score": 145,
      "match_reasons": [
        "From your home country",
        "Long-term expat (knows the area well)",
        "Speaks English, Swahili",
        "Local expert available to help",
        "Available to help"
      ],
      "home_country": "Kenya",
      "is_local_expert": true,
      "helper_rating": "0.00"
    },
    {
      "user": {
        "id": 3,
        "username": "david_visitor"
      },
      "compatibility_score": 90,
      "match_reasons": [
        "From your home country",
        "Fellow traveler with overlapping dates",
        "Speaks English, Swahili",
        "Available to help"
      ],
      "travel_status": "traveling"
    }
  ]
}
```

#### **Compatibility Score Breakdown:**
- **Base (50)**: Same home country + same location
- **Travel Status Bonus (15-40)**: Complementary travel statuses
- **Language Bonus (20 per language)**: Common languages spoken
- **Helper Bonus (25-40)**: Local expert or available to help
- **Rating Bonus (30)**: Helper rating >= 4.0
- **Activity Bonus (10)**: Recent login activity

### **Test 8.5: Emergency Network**

```bash
curl -X GET http://localhost:8000/api/discover/emergency-network/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "message": "Your emergency network: 2 trusted countrymates",
  "location": "London, United Kingdom",
  "emergency_contacts": [
    {
      "user": {
        "id": 2,
        "username": "mary_expert",
        "first_name": "Mary",
        "last_name": "Wanjiku"
      },
      "home_country": "Kenya",
      "is_available_to_help": true,
      "is_local_expert": true,
      "helper_rating": "0.00",
      "years_in_current_location": 3
    },
    {
      "user": {
        "id": 3,
        "username": "david_visitor"
      },
      "home_country": "Kenya",
      "is_available_to_help": true,
      "travel_status": "traveling"
    }
  ],
  "note": "These are fellow countrymates who are available to help in your area"
}
```

### **Test 8.6: Location Statistics**

```bash
curl -X GET http://localhost:8000/api/discover/location-stats/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "location": {
    "home_country": "Kenya",
    "current_location": "London, United Kingdom"
  },
  "local_network": {
    "total_countrymates": 2,
    "travelers": 1,
    "residents": 0,
    "expats": 1,
    "local_experts": 1,
    "available_helpers": 2
  },
  "global_network_size": 3,
  "insights": [
    "Small but growing community: 2 people from Kenya",
    "1 fellow travelers currently in the area",
    "1 verified local experts available to help"
  ]
}
```

---

## ⚙️ **9. TRAVEL STATUS MANAGEMENT**

### **Test 9.1: Get My Travel Status**

```bash
curl -X GET http://localhost:8000/api/travel-status/my-status/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "travel_status": "traveling",
  "travel_dates": {
    "start": "2025-01-10",
    "end": "2025-02-10"
  },
  "location": {
    "home_country": "Kenya",
    "home_city": "Nairobi",
    "current_country": "United Kingdom",
    "current_city": "London"
  },
  "preferences": {
    "is_available_to_help": true,
    "is_local_expert": false,
    "languages_spoken": ["English", "Swahili", "Kikuyu"],
    "expertise_areas": []
  },
  "stats": {
    "helper_rating": 0.0,
    "help_requests_fulfilled": 0,
    "years_in_current_location": null
  }
}
```

### **Test 9.2: Update Travel Status (Triggers Notifications)**

```bash
curl -X POST http://localhost:8000/api/travel-status/update-status/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "travel_status": "traveling",
    "travel_start_date": "2025-01-12",
    "travel_end_date": "2025-02-12",
    "is_available_to_help": true
  }'
```

🔔 **This triggers notifications to nearby countrymates!**

**Expected Response:**
```json
{
  "message": "Travel status updated successfully",
  "travel_status": "traveling",
  "travel_dates": {
    "start": "2025-01-12",
    "end": "2025-02-12"
  },
  "available_to_help": true
}
```

### **Test 9.3: Update Helper Preferences**

```bash
curl -X POST http://localhost:8000/api/travel-status/update-preferences/ \
  -H "Authorization: Bearer YOUR_MARY_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_available_to_help": true,
    "is_local_expert": true,
    "languages_spoken": ["English", "Swahili", "Arabic", "French"],
    "expertise_areas": ["transportation", "food", "accommodation", "culture", "shopping", "nightlife"],
    "years_in_current_location": 4
  }'
```

---

## 🔔 **10. WEBSOCKET REAL-TIME NOTIFICATIONS**

### **Test 10.1: Connect to WebSocket**

#### **Method 1: Browser Console (Recommended)**

1. **Open Browser Developer Tools** (F12)
2. **Go to Console tab**
3. **Run this JavaScript:**

```javascript
// Replace with actual JWT token
const token = 'YOUR_JWT_TOKEN_HERE';
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

ws.onopen = () => {
    console.log('✅ Connected to Jamii Spot notifications');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📩 Notification received:', data);
    
    // Handle different notification types
    switch(data.notification_type) {
        case 'friend_request_received':
            console.log(`👋 Friend request from ${data.data.from_user_username}`);
            break;
        case 'friend_request_accepted':
            console.log(`🎉 ${data.data.new_friend_username} accepted your friend request!`);
            break;
        case 'countrymate_traveling_nearby':
            console.log(`🌍 ${data.data.username} from ${data.data.home_country} is traveling nearby`);
            break;
        case 'location_search_performed':
            console.log(`🔍 Discovery search: ${data.message}`);
            break;
        case 'friend_new_story':
            console.log(`📱 ${data.data.sender_username} posted a new story`);
            break;
        case 'story_processing_complete':
            console.log(`✅ Your ${data.data.media_type} story is ready!`);
            break;
        default:
            console.log(`📨 ${data.type}: ${data.message}`);
    }
};

ws.onerror = (error) => console.error('❌ WebSocket error:', error);
ws.onclose = () => console.log('🔌 WebSocket connection closed');
```

#### **Method 2: Command Line (wscat)**

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c "ws://localhost:8000/ws/notifications/?token=YOUR_JWT_TOKEN"
```

#### **Method 3: Postman WebSocket**

1. Create new **WebSocket Request** in Postman
2. URL: `ws://localhost:8000/ws/notifications/?token=YOUR_JWT_TOKEN`
3. Click **Connect**
4. Monitor real-time messages

### **Test 10.2: Trigger Notifications**

#### **Setup Multiple WebSocket Connections**

1. **Connect Mary to WebSocket** (Browser Console):
```javascript
const maryToken = 'MARY_JWT_TOKEN';
const maryWs = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${maryToken}`);
maryWs.onmessage = (event) => console.log('Mary received:', JSON.parse(event.data));
```

2. **Connect John to WebSocket**:
```javascript
const johnToken = 'JOHN_JWT_TOKEN';
const johnWs = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${johnToken}`);
johnWs.onmessage = (event) => console.log('John received:', JSON.parse(event.data));
```

#### **Trigger Friend Request Notification**

```bash
# John sends friend request to David
curl -X POST http://localhost:8000/api/friend-requests/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_user": 3
  }'
```

**David's WebSocket receives:**
```json
{
  "type": "notification",
  "notification_type": "friend_request_received",
  "message": "john_traveler sent you a friend request",
  "data": {
    "friend_request_id": 2,
    "from_user_id": 1,
    "from_user_username": "john_traveler",
    "from_user_avatar": null,
    "timestamp": "2025-01-12T13:00:00Z"
  }
}
```

#### **Trigger Travel Status Notification**

```bash
# John updates travel status
curl -X POST http://localhost:8000/api/travel-status/update-status/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "travel_status": "traveling",
    "travel_start_date": "2025-01-15",
    "travel_end_date": "2025-02-15"
  }'
```

**Mary's WebSocket receives:**
```json
{
  "type": "notification",
  "notification_type": "countrymate_traveling_nearby",
  "message": "john_traveler from Kenya is now traveling in your area",
  "data": {
    "user_id": 1,
    "username": "john_traveler",
    "home_country": "Kenya",
    "travel_status": "traveling",
    "current_location": "London, United Kingdom",
    "available_to_help": true,
    "travel_dates": {
      "start": "2025-01-15",
      "end": "2025-02-15"
    }
  },
  "timestamp": "2025-01-12T13:05:00Z"
}
```

#### **Discovery Activity Notification**

When John performs a discovery search, he receives:
```json
{
  "type": "discovery_activity",
  "notification_type": "location_search_performed",
  "message": "Found 2 people from Kenya",
  "data": {
    "search_type": "countrymates_nearby",
    "results_count": 2,
    "location": "London, United Kingdom"
  },
  "timestamp": "2025-01-12T13:10:00Z"
}
```

---

## ❌ **11. ERROR HANDLING & SECURITY TESTS**

### **Test 11.1: Authentication Errors**

#### **Unauthorized Access**
```bash
curl -X GET http://localhost:8000/api/discover/countrymates-nearby/
# No Authorization header
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### **Invalid JWT Token**
```bash
curl -X GET http://localhost:8000/api/discover/countrymates-nearby/ \
  -H "Authorization: Bearer invalid_token_12345"
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [...]
}
```

### **Test 11.2: Permission Tests**

#### **Edit Other User's Profile**
```bash
curl -X PATCH http://localhost:8000/api/profiles/2/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Trying to hack Mary'\''s profile!"
  }'
```

**Expected Response (403 Forbidden):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### **Accept Friend Request You Didn't Receive**
```bash
curl -X POST http://localhost:8000/api/friend-requests/1/accept/ \
  -H "Authorization: Bearer YOUR_DAVID_JWT_TOKEN"
```

**Expected Response (403 Forbidden)**

### **Test 11.3: Business Logic Validation**

#### **Send Friend Request to Self**
```bash
curl -X POST http://localhost:8000/api/friend-requests/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_user": 1
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "non_field_errors": ["You cannot send a friend request to yourself."]
}
```

#### **Duplicate Friend Request**
```bash
# Send same friend request twice
curl -X POST http://localhost:8000/api/friend-requests/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_user": 2
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "non_field_errors": ["A friend request already exists."]
}
```

---

## 📊 **12. PERFORMANCE & LOAD TESTING**

### **Test 12.1: Response Time Testing**

#### **Time API Responses**
```bash
# Test countrymate discovery performance
time curl -X GET http://localhost:8000/api/discover/countrymates-nearby/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Test smart matching performance
time curl -X GET http://localhost:8000/api/discover/smart-matches/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected**: Response times under 500ms for small datasets

### **Test 12.2: Pagination Testing**

#### **Test Limit Parameters**
```bash
# Small limit
curl -X GET "http://localhost:8000/api/discover/smart-matches/?limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Large limit (should be capped at 50)
curl -X GET "http://localhost:8000/api/discover/smart-matches/?limit=100" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### **Test 12.3: Concurrent Requests**

#### **Run Multiple Simultaneous Requests**
```bash
# Run these in parallel (multiple terminals)
curl -X GET http://localhost:8000/api/discover/countrymates-nearby/ \
  -H "Authorization: Bearer USER1_TOKEN" &

curl -X GET http://localhost:8000/api/discover/countrymates-nearby/ \
  -H "Authorization: Bearer USER2_TOKEN" &

curl -X GET http://localhost:8000/api/discover/countrymates-nearby/ \
  -H "Authorization: Bearer USER3_TOKEN" &

wait
```

---

## 🧪 **13. ADVANCED TESTING SCENARIOS**

### **Test 13.1: Multi-Country Filtering**

#### **Create User from Different Country**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "sarah_nigerian",
    "email": "sarah@example.com",
    "password": "securepass123",
    "first_name": "Sarah",
    "last_name": "Adebayo"
  }'
```

#### **Setup Nigerian Profile**
```bash
curl -X PATCH http://localhost:8000/api/profiles/4/ \
  -H "Authorization: Bearer SARAH_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Nigerian businesswoman visiting London",
    "home_country": "Nigeria",
    "home_city": "Lagos",
    "current_country": "United Kingdom",
    "current_city": "London",
    "travel_status": "traveling",
    "travel_start_date": "2025-01-08",
    "travel_end_date": "2025-01-22",
    "is_available_to_help": true,
    "languages_spoken": ["English", "Yoruba", "Igbo"],
    "is_local_expert": false
  }'
```

#### **Test Country Filtering**
```bash
curl -X GET http://localhost:8000/api/discover/countrymates-nearby/ \
  -H "Authorization: Bearer SARAH_JWT_TOKEN"
```

**Expected Response (Nigerian should find 0 Kenyan countrymates):**
```json
{
  "message": "Found 0 people from Nigeria in London",
  "location": {
    "home_country": "Nigeria",
    "current_location": "London, United Kingdom"
  },
  "statistics": {
    "total_countrymates": 0,
    "travelers": 0,
    "residents": 0,
    "expats": 0,
    "local_experts": 0,
    "available_helpers": 0
  },
  "countrymates": []
}
```

### **Test 13.2: Date Overlap Algorithm**

#### **Create User with Non-Overlapping Dates**
```bash
# Create user traveling at different time
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "peter_future",
    "email": "peter@example.com",
    "password": "securepass123",
    "first_name": "Peter",
    "last_name": "Mwangi"
  }'

# Setup profile with future travel dates
curl -X PATCH http://localhost:8000/api/profiles/5/ \
  -H "Authorization: Bearer PETER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "home_country": "Kenya",
    "current_country": "United Kingdom",
    "current_city": "London",
    "travel_status": "traveling",
    "travel_start_date": "2025-06-01",
    "travel_end_date": "2025-06-30"
  }'
```

#### **Test Travel Buddy Date Matching**
```bash
# John should not find Peter as travel buddy (non-overlapping dates)
curl -X GET http://localhost:8000/api/discover/travel-buddies/ \
  -H "Authorization: Bearer YOUR_JOHN_JWT_TOKEN"
```

---

## 🔧 **14. DEBUGGING & MONITORING**

### **Test 14.1: Server Logs**

#### **Start Server with Verbose Logging**
```bash
python manage.py runserver --verbosity=2
```

#### **Monitor API Logs**
Watch for these log entries:
- User authentication
- WebSocket connections
- Discovery searches
- Notification sending
- Encryption key generation

### **Test 14.2: Database State Verification**

#### **Check Database State**
```bash
python manage.py shell
```

```python
# In Django shell
from api.models import Profile, FriendRequest, Conversation, Message
from django.contrib.auth.models import User

# Check user profiles
profiles = Profile.objects.all().values()
print("Profiles:", list(profiles))

# Check friend requests
friend_requests = FriendRequest.objects.all().values()
print("Friend Requests:", list(friend_requests))

# Check conversations
conversations = Conversation.objects.all().values()
print("Conversations:", list(conversations))

# Check travel statuses
travel_statuses = Profile.objects.values('user__username', 'travel_status', 'home_country', 'current_city')
print("Travel Statuses:", list(travel_statuses))
```

### **Test 14.3: WebSocket Connection Monitoring**

#### **Monitor WebSocket Connections**
```bash
# Check if Redis is running (required for WebSocket)
redis-cli ping

# Monitor Redis WebSocket channels
redis-cli monitor
```

---

## ✅ **15. COMPREHENSIVE TEST CHECKLIST**

### **Core Features Working:**
- [ ] User registration creates profiles automatically
- [ ] JWT authentication protects all endpoints
- [ ] Profile updates save travel data correctly
- [ ] Friend requests send real-time notifications
- [ ] Countrymate discovery filters by home country and location
- [ ] Local expert identification works with expertise areas
- [ ] Travel buddy matching considers date overlap
- [ ] Smart matching provides compatibility scores and reasons
- [ ] Emergency network returns available helpers
- [ ] Location statistics provide accurate insights

### **Real-time Features:**
- [ ] WebSocket connections establish successfully
- [ ] Friend request notifications work
- [ ] Friend acceptance notifications work
- [ ] Travel status change notifications work
- [ ] Discovery activity notifications work
- [ ] Story posting notifications work
- [ ] Message notifications work

### **Security & Permissions:**
- [ ] Unauthorized requests return 401
- [ ] Invalid tokens return 401
- [ ] Users can only edit own profiles
- [ ] Users can only accept friend requests sent to them
- [ ] Cross-user data access is properly restricted

### **Data Integrity:**
- [ ] Profile completeness scores calculate correctly
- [ ] Travel dates validate properly
- [ ] Language arrays store and retrieve correctly
- [ ] Travel status choices are enforced
- [ ] Country filtering works across all discovery endpoints

### **Performance:**
- [ ] API responses under 1000ms
- [ ] Pagination limits are enforced (max 50)
- [ ] Concurrent requests handled properly
- [ ] WebSocket supports multiple connections

### **Business Logic:**
- [ ] Only travelers can find travel buddies
- [ ] Country matching is exact (Kenya ≠ Nigeria)
- [ ] Date overlap algorithm works correctly
- [ ] Helper availability is respected
- [ ] Local expert requirements are enforced

---

## 🎉 **SUCCESS CRITERIA**

**✅ ALL TESTS PASS:** The Jamii Spot API is fully operational!

### **Core App Vision Achieved:**
*"Enabling people to connect with people from the same country when they visit another country"*

### **Key Success Indicators:**

1. **Discovery Works:** Users can find countrymates in their current location
2. **Smart Matching:** Compatibility algorithm provides relevant matches with clear reasons
3. **Helper Network:** Local experts and helpers are identifiable and accessible
4. **Real-time:** All social interactions trigger appropriate notifications
5. **Security:** E2E encryption is set up and JWT authentication is enforced
6. **Performance:** All endpoints respond quickly with proper pagination

### **Ready for:**
- Frontend integration
- Production deployment
- User acceptance testing
- Performance optimization
- Feature expansion

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues:**

1. **Server won't start:**
   - Check dependencies: `pip install -r requirements.txt`
   - Check Python version compatibility
   - Verify database migrations: `python manage.py migrate`

2. **JWT Token errors:**
   - Tokens expire after 15 minutes (default)
   - Use refresh token to get new access token
   - Check token format and Bearer prefix

3. **WebSocket connection fails:**
   - Ensure Redis is running
   - Check WebSocket URL format
   - Verify JWT token in query parameter

4. **No countrymates found:**
   - Verify users have matching `home_country`
   - Check `current_city` matches exactly
   - Ensure test users are in database

5. **Notifications not received:**
   - WebSocket must be connected before triggering action
   - Check browser console for WebSocket errors
   - Verify user is in correct notification group

### **Debug Commands:**

```bash
# Check server status
curl -I http://localhost:8000/admin/

# Test WebSocket endpoint
wscat -c "ws://localhost:8000/ws/notifications/?token=test"

# Check Redis connection
redis-cli ping

# Verify database state
python manage.py dbshell
.tables
```

---

## 🌟 **POSTMAN COLLECTION FEATURES**

The included Postman collection provides:

- **Automated JWT token management** for multiple users
- **Comprehensive test assertions** for all endpoints
- **Real-time notification testing guidance**
- **Performance monitoring** with response time checks
- **Error scenario testing** with expected failure cases
- **Variable management** for test data persistence
- **Complete user journey simulations**

**Import the collection and run tests in sequence for best results!**

---

## 📞 **NEXT STEPS**

After successful API testing:

1. **Frontend Integration**: Connect React/Vue/Angular frontend
2. **Mobile App Integration**: Test with React Native/Flutter
3. **Production Setup**: Configure production settings and deployment
4. **Performance Optimization**: Add caching and database optimization
5. **Feature Expansion**: Add more countries, languages, and expert categories

**🚀 The Jamii Spot API is ready to connect travelers worldwide!**
