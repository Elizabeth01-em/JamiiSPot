# Jamii Spot API Documentation

Welcome to the Jamii Spot API documentation. This document provides a detailed overview of the available API endpoints, their functionalities, and the expected data formats.

## Table of Contents

- [Authentication](#authentication)
- [Profiles](#profiles)
- [Friend Requests](#friend-requests)
- [Communities](#communities)
- [Stories](#stories)
- [Messaging](#messaging)
- [Discovery](#discovery)

## Authentication

### Register a new user

- **Endpoint:** `POST /api/auth/register/`
- **Description:** Creates a new user and an associated profile.
- **Permissions:** AllowAny
- **Request Body:**
  ```json
  {
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "strongpassword",
    "first_name": "New",
    "last_name": "User"
  }
  ```
- **Response:**
  - `201 CREATED`: User created successfully.
    ```json
    {
      "username": "newuser",
      "email": "newuser@example.com",
      "first_name": "New",
      "last_name": "User"
    }
    ```
  - `400 BAD REQUEST`: If the username or email already exists, or if the password is too common.

### Obtain an auth token

- **Endpoint:** `POST /api/auth/token/`
- **Description:** Authenticates a user and returns an access and refresh token pair.
- **Permissions:** AllowAny
- **Request Body:**
  ```json
  {
    "username": "existinguser",
    "password": "userpassword"
  }
  ```
- **Response:**
  - `200 OK`: Authentication successful.
    ```json
    {
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
  - `401 UNAUTHORIZED`: If the credentials are invalid.

### Refresh an auth token

- **Endpoint:** `POST /api/auth/token/refresh/`
- **Description:** Takes a refresh token and returns a new access token.
- **Permissions:** AllowAny
- **Request Body:**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response:**
  - `200 OK`: Token refreshed successfully.
    ```json
    {
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

---

## Profiles

The `Profile` model represents a user's public profile, including their bio, avatar, location, interests, and friends.

- **Endpoint:** `/api/profiles/`
- **ViewSet:** `ProfileViewSet`
- **Serializer:** `ProfileSerializer`

### List profiles

- **Endpoint:** `GET /api/profiles/`
- **Description:** Retrieves a list of all user profiles.
- **Permissions:** IsAuthenticated

### Retrieve a profile

- **Endpoint:** `GET /api/profiles/{id}/`
- **Description:** Retrieves a specific user profile by ID.
- **Permissions:** IsAuthenticated
- **Response Body:** An example `Profile` object.

### Update a profile

- **Endpoint:** `PUT /api/profiles/{id}/` or `PATCH /api/profiles/{id}/`
- **Description:** Updates a user's profile. You can only update your own profile.
- **Permissions:** IsAuthenticated, IsOwnerOrReadOnly
- **Request Body:** A subset of the fields in the `Profile` object.
  ```json
  {
    "bio": "A new bio",
    "home_country": "Kenya",
    "current_city": "Nairobi",
    "travel_status": "resident",
    "languages_spoken": ["English", "Swahili", "Kikuyu"],
    "is_available_to_help": true
  }
  ```

### Delete a profile

- **Endpoint:** `DELETE /api/profiles/{id}/`
- **Description:** Deletes a user's profile. You can only delete your own profile.
- **Permissions:** IsAuthenticated, IsOwnerOrReadOnly

### The Profile Object

The `Profile` object has the following structure:

```json
{
  "user": {
    "id": 1,
    "username": "jules",
    "first_name": "Jules",
    "last_name": "Doe"
  },
  "bio": "Software engineer and travel enthusiast.",
  "avatar": "https://example.com/avatar.jpg",
  "home_country": "Kenya",
  "home_city": "Nairobi",
  "current_country": "USA",
  "current_city": "New York",
  "interests": ["coding", "hiking", "photography"],
  "friends": [2, 3, 5],
  "completeness_score": 100,
  "travel_status": "traveling",
  "travel_status_display": "Traveling",
  "is_traveling": true,
  "travel_start_date": "2025-01-01",
  "travel_end_date": "2025-02-01",
  "is_available_to_help": true,
  "languages_spoken": ["English", "Swahili"],
  "years_in_current_location": 1,
  "is_local_expert": false,
  "expertise_areas": ["food", "history"],
  "helper_rating": "4.50",
  "help_requests_fulfilled": 10,
  "days_in_current_location": 30
}
```

- **`user`**: (Object) The associated user object.
- **`bio`**: (String) A short biography.
- **`avatar`**: (String) A URL to the user's avatar image.
- **`home_country`**, **`home_city`**: (String) The user's home location.
- **`current_country`**, **`current_city`**: (String) The user's current location.
- **`interests`**: (Array of Strings) A list of the user's interests.
- **`friends`**: (Array of Integers) A list of user IDs for the user's friends.
- **`completeness_score`**: (Integer) A score from 0-100 indicating how complete the profile is.
- **`travel_status`**: (String) The user's travel status. Can be `not_traveling`, `traveling`, or `resident`.
- **`travel_status_display`**: (String) A human-readable version of the travel status.
- **`is_traveling`**: (Boolean) True if the user is currently traveling.
- **`travel_start_date`**, **`travel_end_date`**: (String) The start and end dates of the user's travel.
- **`is_available_to_help`**: (Boolean) True if the user is available to help others.
- **`languages_spoken`**: (Array of Strings) A list of languages the user speaks.
- **`years_in_current_location`**: (Integer) The number of years the user has been in their current location.
- **`is_local_expert`**: (Boolean) True if the user is a verified local expert.
- **`expertise_areas`**: (Array of Strings) A list of areas where the user has expertise.
- **`helper_rating`**: (String) The user's rating as a helper.
- **`help_requests_fulfilled`**: (Integer) The number of help requests the user has fulfilled.
- **`days_in_current_location`**: (Integer) The number of days the user has been in their current location.

---

## Friend Requests

The `FriendRequest` model manages the process of users becoming friends.

- **Endpoint:** `/api/friend-requests/`
- **ViewSet:** `FriendRequestViewSet`
- **Serializer:** `FriendRequestSerializer`

### List friend requests

- **Endpoint:** `GET /api/friend-requests/`
- **Description:** Lists friend requests sent or received by the current user.
- **Permissions:** IsAuthenticated

### Send a friend request

- **Endpoint:** `POST /api/friend-requests/`
- **Description:** Sends a friend request to another user.
- **Permissions:** IsAuthenticated
- **Request Body:**
  ```json
  {
    "to_user": 2
  }
  ```

### Accept a friend request

- **Endpoint:** `POST /api/friend-requests/{id}/accept/`
- **Description:** Accepts a pending friend request.
- **Permissions:** IsAuthenticated, IsReceiver

### Reject a friend request

- **Endpoint:** `POST /api/friend-requests/{id}/reject/`
- **Description:** Rejects a pending friend request.
- **Permissions:** IsAuthenticated, IsReceiver

### The FriendRequest Object

The `FriendRequest` object has the following structure:

```json
{
  "id": 1,
  "from_user": "jules",
  "to_user": 2,
  "status": "pending",
  "created_at": "2025-01-01T12:00:00Z"
}
```

- **`id`**: (Integer) The ID of the friend request.
- **`from_user`**: (String) The username of the user who sent the request.
- **`to_user`**: (Integer) The ID of the user who received the request.
- **`status`**: (String) The status of the request. Can be `pending`, `accepted`, or `rejected`.
- **`created_at`**: (String) The timestamp when the request was created.

---

## Communities

The `Community` model represents a group of users with shared interests.

- **Endpoint:** `/api/communities/`
- **ViewSet:** `CommunityViewSet`
- **Serializer:** `CommunitySerializer`

### List communities

- **Endpoint:** `GET /api/communities/`
- **Description:** Retrieves a list of all communities.
- **Permissions:** IsAuthenticated

### Create a community

- **Endpoint:** `POST /api/communities/`
- **Description:** Creates a new community. The creator becomes an admin.
- **Permissions:** IsAuthenticated
- **Request Body:**
  ```json
  {
    "name": "Django Developers",
    "description": "A community for Django enthusiasts."
  }
  ```

### Retrieve a community

- **Endpoint:** `GET /api/communities/{id}/`
- **Description:** Retrieves a specific community by ID.
- **Permissions:** IsAuthenticated

### Update a community

- **Endpoint:** `PUT /api/communities/{id}/` or `PATCH /api/communities/{id}/`
- **Description:** Updates a community's details. Only admins can update.
- **Permissions:** IsAuthenticated, IsCommunityAdminOrReadOnly

### Delete a community

- **Endpoint:** `DELETE /api/communities/{id}/`
- **Description:** Deletes a community. Only admins can delete.
- **Permissions:** IsAuthenticated, IsCommunityAdminOrReadOnly

### The Community Object

The `Community` object has the following structure:

```json
{
  "id": 1,
  "name": "Django Developers",
  "profile_image": "https://example.com/community.jpg",
  "description": "A community for Django enthusiasts.",
  "created_by": "jules",
  "created_at": "2025-01-01T12:00:00Z",
  "is_channel": false,
  "member_count": 25
}
```

- **`id`**: (Integer) The ID of the community.
- **`name`**: (String) The name of the community.
- **`profile_image`**: (String) A URL to the community's profile image.
- **`description`**: (String) A description of the community.
- **`created_by`**: (String) The username of the user who created the community.
- **`created_at`**: (String) The timestamp when the community was created.
- **`is_channel`**: (Boolean) True if the community is a channel (only admins can post).
- **`member_count`**: (Integer) The number of members in the community.

---

## Stories

The `StoryPost` model represents a user's story, which can contain multiple items (images or videos).

- **Endpoint:** `/api/stories/`
- **ViewSet:** `StoryPostViewSet`
- **Serializer:** `StoryPostSerializer`

### List stories

- **Endpoint:** `GET /api/stories/`
- **Description:** Retrieves a list of all stories.
- **Permissions:** IsAuthenticated

### Create a story

- **Endpoint:** `POST /api/stories/`
- **Description:** Creates a new story. The media is processed asynchronously.
- **Permissions:** IsAuthenticated
- **Request Body (form-data):**
  - `media_file`: The image or video file.
  - `media_type`: 'image' or 'video'.
  - `start_time` (optional): For video trimming.
  - `end_time` (optional): For video trimming.
- **Response:**
  - `202 ACCEPTED`: The story is being processed.

### The StoryPost Object

The `StoryPost` object has the following structure:

```json
{
  "id": 1,
  "sender": "jules",
  "created_at": "2025-01-01T12:00:00Z",
  "items": [
    {
      "id": 1,
      "media_file": "https://example.com/story.jpg",
      "media_type": "image",
      "duration_seconds": 10,
      "status": "processed"
    }
  ],
  "viewers": [2, 3]
}
```

- **`id`**: (Integer) The ID of the story post.
- **`sender`**: (String) The username of the user who posted the story.
- **`created_at`**: (String) The timestamp when the story was created.
- **`items`**: (Array of Objects) A list of `StoryItem` objects.
- **`viewers`**: (Array of Integers) A list of user IDs who have viewed the story.

### The StoryItem Object

The `StoryItem` object has the following structure:

```json
{
  "id": 1,
  "media_file": "https://example.com/story.jpg",
  "media_type": "image",
  "duration_seconds": 10,
  "status": "processed"
}
```

- **`id`**: (Integer) The ID of the story item.
- **`media_file`**: (String) A URL to the media file.
- **`media_type`**: (String) The type of media. Can be `image` or `video`.
- **`duration_seconds`**: (Integer) The duration of the story item in seconds.
- **`status`**: (String) The processing status of the media. Can be `pending_upload`, `processing`, or `processed`.

---

## Messaging

The messaging system consists of conversations, messages, and encryption keys.

### Encryption Keys

- **Endpoint:** `/api/encryption-keys/`
- **ViewSet:** `UserEncryptionKeyViewSet`
- **Serializer:** `UserEncryptionKeySerializer`

#### Get your encryption key

- **Endpoint:** `GET /api/encryption-keys/`
- **Description:** Retrieves the current user's encryption key.

#### Create an encryption key

- **Endpoint:** `POST /api/encryption-keys/`
- **Description:** Creates a new RSA key pair for the user. The private key is returned only once.

### Public Keys

- **Endpoint:** `/api/public-keys/`
- **View:** `PublicKeyAPIView`
- **Serializer:** `UserEncryptionKeySerializer`

#### Get public keys for users

- **Endpoint:** `GET /api/public-keys/?user_ids=1,2,3`
- **Description:** Retrieves the public keys for a list of user IDs.

### Conversations

- **Endpoint:** `/api/conversations/`
- **ViewSet:** `ConversationViewSet`
- **Serializer:** `ConversationSerializer`

#### List conversations

- **Endpoint:** `GET /api/conversations/`
- **Description:** Lists all conversations the current user is a participant in.

#### Create a conversation

- **Endpoint:** `POST /api/conversations/`
- **Description:** Creates a new conversation (private, group, or community).
- **Request Body:**
  ```json
  {
    "conversation_type": "group",
    "name": "My Group",
    "participant_ids": [2, 3]
  }
  ```

### Messages

- **Endpoint:** `/api/messages/`
- **ViewSet:** `MessageViewSet`
- **Serializer:** `MessageSerializer`

#### List messages in a conversation

- **Endpoint:** `GET /api/conversations/{id}/messages/`
- **Description:** Retrieves messages for a specific conversation.

#### Send a message

- **Endpoint:** `POST /api/messages/`
- **Description:** Sends a message to a conversation.
- **Request Body:**
  ```json
  {
    "conversation": 1,
    "content": "Hello, world!"
  }
  ```

### The UserEncryptionKey Object

```json
{
  "user": "jules",
  "public_key": "ssh-rsa AAAA...",
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

### The Conversation Object

```json
{
  "id": 1,
  "conversation_type": "group",
  "participants": [
    { "id": 1, "username": "jules" },
    { "id": 2, "username": "jane" }
  ],
  "participant_details": [
    {
      "user": { "id": 1, "username": "jules" },
      "role": "admin",
      "joined_at": "2025-01-01T12:00:00Z",
      "left_at": null,
      "is_muted": false,
      "last_seen_message": null,
      "encrypted_conversation_key": "..."
    }
  ],
  "community": null,
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z",
  "name": "My Group",
  "description": "A group for my friends.",
  "last_message": {
    "id": 1,
    "sender": "jules",
    "message_type": "text",
    "timestamp": "2025-01-01T12:00:00Z"
  },
  "unread_count": 0
}
```

### The Message Object

```json
{
  "id": 1,
  "conversation": 1,
  "sender": { "id": 1, "username": "jules" },
  "message_type": "text",
  "encrypted_content": "...",
  "media_file": null,
  "timestamp": "2025-01-01T12:00:00Z",
  "edited_at": null,
  "is_deleted": false,
  "deleted_at": null,
  "reply_to": null,
  "reply_to_message": null,
  "is_read": true,
  "read_count": 1
}
```

---

## Discovery

The discovery endpoints help users find other users based on location, travel plans, and interests.

### Discovery Actions

- **Endpoint:** `/api/discover/`
- **ViewSet:** `DiscoveryViewSet`

#### Find countrymates nearby

- **Endpoint:** `GET /api/discover/countrymates-nearby/`
- **Description:** Finds people from your home country in your current location.

#### Find local experts

- **Endpoint:** `GET /api/discover/local-experts/`
- **Description:** Finds verified local experts in your current location.

#### Find travel buddies

- **Endpoint:** `GET /api/discover/travel-buddies/`
- **Description:** Finds fellow travelers from your country with overlapping travel dates.

#### Get smart matches

- **Endpoint:** `GET /api/discover/smart-matches/`
- **Description:** Gets AI-powered matches based on multiple compatibility factors.

#### Get emergency network

- **Endpoint:** `GET /api/discover/emergency-network/`
- **Description:** Finds trusted countrymates who can help in emergencies.

#### Get location stats

- **Endpoint:** `GET /api/discover/location-stats/`
- **Description:** Gets statistics about your countrymates in your current location.

#### Update travel status

- **Endpoint:** `POST /api/discover/update-travel-status/`
- **Description:** Updates your travel status and dates.
- **Request Body:**
  ```json
  {
    "travel_status": "traveling",
    "travel_start_date": "2025-01-15",
    "travel_end_date": "2025-01-30"
  }
  ```

### Travel Status

- **Endpoint:** `/api/travel-status/`
- **ViewSet:** `TravelStatusViewSet`

#### Get my status

- **Endpoint:** `GET /api/travel-status/my-status/`
- **Description:** Gets the current user's travel status and preferences.

#### Update preferences

- **Endpoint:** `POST /api/travel-status/update-preferences/`
- **Description:** Updates your travel preferences and helper settings.
- **Request Body:**
  ```json
  {
    "is_available_to_help": true,
    "languages_spoken": ["English", "Swahili"]
  }
  ```
- **Response Body:**
  ```json
  {
    "message": "Preferences updated successfully",
    "preferences": {
        "is_available_to_help": true,
        "is_local_expert": false,
        "languages_spoken": [
            "English",
            "Swahili"
        ],
        "expertise_areas": [],
        "years_in_current_location": 0
    }
  }
  ```