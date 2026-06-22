# 🚀 ASHWIN VIP PANNEL - Android App Integration Guide

## 📌 BASE SERVER URL
```
https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev
```

---

## 🔐 KEY LOGIN FLOW FOR ANDROID APP

### **Step 1: Check Server Status**
**Endpoint:** `GET /apk_connect`

**URL:** `https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev/apk_connect`

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
  "server_time": "2026-06-22T16:30:00"
}
```

---

### **Step 2: User Login with License Key ONLY** ⭐ **NO USERNAME/PASSWORD**
**Endpoint:** `POST /api/login`

**URL:** `https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev/api/login`

**Request Body (Form or JSON):**
```
Content-Type: application/x-www-form-urlencoded
key=ABCD1234EFGH5678

OR

Content-Type: application/json
{"key": "ABCD1234EFGH5678"}
```

**Success Response (HTTP 200):**
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

**Error Responses:**

❌ Invalid Key (HTTP 401):
```json
{
  "success": false,
  "error": "Invalid key"
}
```

❌ Key Already Used (HTTP 403):
```json
{
  "success": false,
  "error": "Key already used"
}
```

❌ Key Expired (HTTP 403):
```json
{
  "success": false,
  "error": "Key has expired"
}
```

---

### **Step 3: Activate Key (After Login)**
**Endpoint:** `POST /use_key`

**URL:** `https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev/use_key`

**Request Body:**
```
Content-Type: application/x-www-form-urlencoded

key=ABCD1234EFGH5678
```

**Required Session Cookie** (from user login)

**Success Response (HTTP 200):**
```json
{
  "success": true,
  "message": "Key used successfully!",
  "balance": 100.50
}
```

**Error Response (HTTP 200 or 403):**
```json
{
  "valid": false,
  "message": "Key has expired"
}
```

---

## 📊 KEY PRICING (INR per key)

| Validity Type | Price | Duration |
|---------------|-------|----------|
| `day` | ₹75 | 1 Day |
| `week` | ₹400 | 7 Days |
| `month` | ₹1500 | 30 Days |
| `session` | ₹25 | 24 Hours |

---

## 💻 ANDROID/KOTLIN IMPLEMENTATION EXAMPLE

### **Complete Key-Only Login Activity**

```kotlin
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import org.json.JSONObject
import java.io.IOException

class LoginActivity : AppCompatActivity() {
    
    private val BASE_URL = "https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev"
    private lateinit var client: OkHttpClient
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)
        
        client = OkHttpClient()
        
        val keyInput = findViewById<EditText>(R.id.license_key)
        val loginButton = findViewById<Button>(R.id.loginBtn)
        
        loginButton.setOnClickListener {
            val key = keyInput.text.toString().trim()
            
            if (key.isEmpty()) {
                Toast.makeText(this, "⚠️ Please enter license key", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            
            performKeyLogin(key)
        }
    }
    
    private fun performKeyLogin(key: String) {
        val formBody = FormBody.Builder()
            .add("key", key)
            .build()
        
        val request = Request.Builder()
            .url("$BASE_URL/api/login")
            .post(formBody)
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    Toast.makeText(
                        this@LoginActivity,
                        "❌ Network Error: ${e.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                val json = response.body?.string() ?: ""
                val jsonObj = JSONObject(json)
                
                runOnUiThread {
                    if (jsonObj.optBoolean("success")) {
                        // ✅ Login successful with key
                        val user = jsonObj.getJSONObject("user")
                        val username = user.getString("username")
                        val balance = user.getDouble("balance")
                        
                        Toast.makeText(
                            this@LoginActivity,
                            "✅ Welcome $username! Balance: ₹$balance",
                            Toast.LENGTH_LONG
                        ).show()
                        
                        // Save user data
                        saveUserData(user)
                        
                        // Open main app
                        startActivity(Intent(this@LoginActivity, MainActivity::class.java))
                        finish()
                    } else {
                        // ❌ Key invalid
                        val error = jsonObj.getString("error")
                        Toast.makeText(this@LoginActivity, "❌ $error", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        })
    }
    
    private fun saveUserData(user: JSONObject) {
        val sharedPref = getSharedPreferences("app_prefs", MODE_PRIVATE)
        sharedPref.edit().apply {
            putInt("user_id", user.getInt("id"))
            putString("username", user.getString("username"))
            putString("role", user.getString("role"))
            putFloat("balance", user.getDouble("balance").toFloat())
            apply()
        }
    }
}
```

---

### **Activity Layout (activity_login.xml)**
```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="20dp"
    android:gravity="center">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="🔑 Enter License Key"
        android:textSize="24sp"
        android:textStyle="bold"
        android:layout_marginBottom="30dp" />

    <EditText
        android:id="@+id/license_key"
        android:layout_width="match_parent"
        android:layout_height="50dp"
        android:hint="Enter your license key"
        android:padding="10dp"
        android:textSize="16sp"
        android:layout_marginBottom="20dp" />

    <Button
        android:id="@+id/loginBtn"
        android:layout_width="match_parent"
        android:layout_height="50dp"
        android:text="LOGIN"
        android:textSize="18sp"
        android:textStyle="bold" />
</LinearLayout>
```

---

## 🔄 COMPLETE APP FLOW

```
┌─────────────────────────────────────────────────────────┐
│  USER OPENS APP                                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  SHOW KEY INPUT DIALOG                                  │
│  "Enter your license key"                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  API: POST /api/login                                   │
│  Parameter: key=LICENSEKEY                              │
│  Validate & Login with key only                         │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
    ✅ VALID & LOGIN                ❌ INVALID
        ↓                               ↓
  Save Session                    Show Error Message
  (user_id, balance)              Retry Key Input
        ↓
┌─────────────────────────────────────────────────────────┐
│  API: POST /use_key                                     │
│  Activate the license key                               │
└─────────────────────────────────────────────────────────┘
        ↓
    ✅ Key Activated
        ↓
  OPEN MAIN APP
  (User logged in & key activated)
```

---

## 📱 TEST LINKS

| Purpose | Link | Method |
|---------|------|--------|
| **Dashboard** | https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev | GET |
| **Check Key API** | https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev/check_key | POST |
| **Login API** | https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev/api/login | POST |
| **Use Key API** | https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev/use_key | POST |
| **APK Connect** | https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev/apk_connect | GET |

---

## 🔑 TEST CREDENTIALS

| Field | Value |
|-------|-------|
| **Username** | ASHWIN |
| **Password** | PUSHKAR2006 |

---

## ⚠️ ERROR HANDLING

Always implement proper error handling:

```kotlin
try {
    if (response.isSuccessful) {
        val json = response.body?.string() ?: ""
        val jsonObj = JSONObject(json)
        
        when {
            jsonObj.optBoolean("valid") || jsonObj.optBoolean("success") -> {
                // ✅ Success
            }
            jsonObj.has("error") -> {
                // ❌ API Error
                val error = jsonObj.getString("error")
                showError(error)
            }
            jsonObj.has("message") -> {
                // ⚠️ Validation Error
                val message = jsonObj.getString("message")
                showError(message)
            }
        }
    } else {
        showError("Server Error: ${response.code}")
    }
} catch (e: Exception) {
    showError("Network Error: ${e.message}")
}
```

---

## 📞 SUPPORT

- **Server Status**: Check `/apk_connect` endpoint
- **Key Issues**: Contact admin at website
- **Server URL**: https://musical-disco-r74vp9gxvwq7fxp94-5000.app.github.dev

**Last Updated:** 2026-06-22
