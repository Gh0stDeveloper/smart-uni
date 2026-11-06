/** OIDC Authorization Code + PKCE, estado y nonce gestionados por Auth.js.
 * Los roles NUNCA llegan de un claim cliente para conceder permisos.
 */
import NextAuth from "next-auth";
import Keycloak from "next-auth/providers/keycloak";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Keycloak({
      issuer: process.env.AUTH_KEYCLOAK_ISSUER,
      clientId: process.env.AUTH_KEYCLOAK_ID,
      clientSecret: process.env.AUTH_KEYCLOAK_SECRET,
      checks: ["pkce", "state", "nonce"],
      authorization: { params: { scope: "openid profile email" } },
    }),
  ],
  session: { strategy: "jwt", maxAge: 1800 },
  callbacks: {
    async jwt({ token, account }) {
      if (account?.access_token && typeof account.expires_at === "number") {
        // Viaja solo dentro de la cookie de sesión cifrada/HttpOnly de Auth.js.
        token.apiAccessToken = account.access_token;
        token.apiExpiresAt = account.expires_at;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = typeof token.sub === "string" ? token.sub : "";
      }
      // Nunca exponer apiAccessToken, refresh_token ni rol concedido por JWT.
      return session;
    },
  },
});
