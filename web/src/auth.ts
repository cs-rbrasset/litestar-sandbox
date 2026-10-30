import { acquireApiToken } from "./msal.ts";
import { client } from "./generated/api/client.gen.ts";

export function installAuth() {
  client.interceptors.request.use(async (request) => {
    const token = await acquireApiToken();
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  });
}
