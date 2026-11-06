# JNI methods use exported symbols based on their exact Java class and names.
-keep class xyz.smartuni.app.NativeBridge { *; }
-keep class xyz.smartuni.app.KeyVault { *; }
-keep class xyz.smartuni.app.EncryptedNotesStore { *; }

# Do not suppress warnings globally. Release build fails if types are missing.

-keep class xyz.smartuni.app.OidcCallbackActivity { *; }
-keep class xyz.smartuni.app.SessionVault { *; }
