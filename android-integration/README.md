# 🚀 ASHWIN VIP PANNEL - Android Integration Guide

## 📱 Complete Android/Java Integration with Retrofit

This folder contains complete Android integration code for connecting your app to the ASHWIN VIP PANNEL Flask backend.

---

## 🔗 **Server Configuration**

**Base URL:**
```
https://web-production-9be7c.up.railway.app
```

---

## 📦 **Required Dependencies**

Add to your `build.gradle` (Module: app):

```gradle
dependencies {
    // Retrofit
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    
    // OkHttp (for logging and interceptors)
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.11.0'
    
    // Gson
    implementation 'com.google.code.gson:gson:2.10.1'
    
    // Coroutines (optional, for async calls)
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.1'
}
```

---

## 📂 **Folder Structure**

```
android-integration/
├── README.md (this file)
├── models/
│   ├── KeyRequest.java
│   ├── LoginResponse.java
│   ├── User.java
│   └── ApiResponse.java
├── api/
│   ├── ApiClient.java
│   ├── ApiService.java
│   └── RetrofitClient.java
├── activities/
│   ├── LoginActivity.java
│   └── MainActivity.java
├── utils/
│   ├── SharedPrefManager.java
│   └── Constants.java
└── interceptors/
    └── AuthInterceptor.java
```

---

## 🔐 **API Endpoints**

### 1️⃣ **Login with License Key**
```
POST /api/login
Content-Type: application/json

{
  "key": "ABCD1234EFGH5678"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Login successful - Key validated",
  "user": {
    "id": 1,
    "username": "ASHWIN",
    "role": "admin",
    "balance": 999900.50
  }
}
```

**Error Response (401/403):**
```json
{
  "success": false,
  "error": "Invalid key"
}
```

---

### 2️⃣ **Check Key Validity**
```
POST /check_key
Content-Type: application/x-www-form-urlencoded

key=ABCD1234EFGH5678
```

**Response:**
```json
{
  "valid": true,
  "key": "ABCD1234EFGH5678",
  "validity_type": "month",
  "expires_at": "2026-07-22 17:30:00"
}
```

---

### 3️⃣ **Use/Activate Key**
```
POST /use_key
Content-Type: application/x-www-form-urlencoded

key=ABCD1234EFGH5678
```

**Response:**
```json
{
  "success": true,
  "message": "Key used successfully!",
  "balance": 100.50
}
```

---

### 4️⃣ **Get Server Status**
```
GET /apk_connect
```

**Response:**
```json
{
  "status": "active",
  "panel": "ASHWIN VIP PANNEL",
  "version": "2.1",
  "api_endpoints": {
    "check_key": "/check_key",
    "use_key": "/use_key",
    "stats": "/api/stats"
  },
  "server_time": "2026-06-22T17:30:00"
}
```

---

## 🛠️ **Implementation Steps**

### **Step 1: Add Models**
Copy all files from `models/` folder to your Android project:
```
app/src/main/java/com/yourpackage/models/
```

### **Step 2: Add API Layer**
Copy all files from `api/` folder:
```
app/src/main/java/com/yourpackage/api/
```

### **Step 3: Add Activities**
Copy login and main activities from `activities/` folder:
```
app/src/main/java/com/yourpackage/activities/
```

### **Step 4: Add Utilities**
Copy utility classes from `utils/` folder:
```
app/src/main/java/com/yourpackage/utils/
```

### **Step 5: Update AndroidManifest.xml**
```xml
<uses-permission android:name="android.permission.INTERNET" />
```

---

## 💻 **Quick Start Example**

```java
// Initialize Retrofit
ApiService apiService = RetrofitClient.getClient().create(ApiService.class);

// Create login request
KeyRequest request = new KeyRequest("YOUR_LICENSE_KEY");

// Make API call
Call<LoginResponse> call = apiService.loginWithKey(request);
call.enqueue(new Callback<LoginResponse>() {
    @Override
    public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
        if (response.isSuccessful() && response.body() != null) {
            LoginResponse loginResponse = response.body();
            if (loginResponse.isSuccess()) {
                // Save user data
                SharedPrefManager.getInstance(context).saveUser(loginResponse.getUser());
                
                // Navigate to main activity
                startActivity(new Intent(LoginActivity.this, MainActivity.class));
                finish();
            } else {
                // Show error
                Toast.makeText(LoginActivity.this, loginResponse.getError(), Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    public void onFailure(Call<LoginResponse> call, Throwable t) {
        Toast.makeText(LoginActivity.this, "Network Error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
    }
});
```

---

## 🔒 **Session Management**

The app automatically manages sessions using:
- **SharedPreferences** for storing user data
- **Cookies** for maintaining server sessions
- **AuthInterceptor** for adding auth headers

---

## 🧪 **Testing**

### **Test Credentials**
- **License Key**: Generate from dashboard
- **Admin Username**: ASHWIN
- **Admin Password**: PUSHKAR2006

### **Test Endpoints**
```
GET https://web-production-9be7c.up.railway.app/apk_connect
POST https://web-production-9be7c.up.railway.app/api/login
```

---

## ⚠️ **Error Handling**

Common error codes:

| Code | Error | Solution |
|------|-------|----------|
| 400 | Missing key | Ensure key is provided |
| 401 | Invalid key | Check key format |
| 403 | Key already used | Use a new key |
| 403 | Key expired | Generate new key |
| 500 | Server error | Check server status |

---

## 🔄 **Complete Flow Diagram**

```
┌─────────────────────────────────────────┐
│  User Opens App                         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Check Server Status (/apk_connect)     │
└─────────────────────────────────────────┘
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
    ✅ ACTIVE              ❌ INACTIVE
        ↓                       ↓
  Show Login Screen      Show Error
        ↓
┌─────────────────────────────────────────┐
│  User Enters License Key                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  POST /api/login (with key)             │
└─────────────────────────────────────────┘
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
    ✅ VALID                ❌ INVALID
        ↓                       ↓
  Save User Data         Show Error
  Save Session           Retry
        ↓
┌─────────────────────────────────────────┐
│  POST /use_key (activate key)           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Open Main Activity                     │
│  User Logged In & Key Activated         │
└─────────────────────────────────────────┘
```

---

## 📞 **Support**

- **Server**: https://web-production-9be7c.up.railway.app
- **Status Check**: /apk_connect
- **Issues**: Check error responses and logs

---

**Last Updated:** 2026-06-24

