# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified
# in ${sdk.dir}/tools/proguard/proguard-android-optimize.txt

# This app is a single WebView wrapper around a bundled asset page, with a
# small JavaScript bridge. Keep the bridge's methods reachable from JS.
-keepclassmembers class com.mattress.checklist.MainActivity$ChecklistBridge {
    public *;
}
