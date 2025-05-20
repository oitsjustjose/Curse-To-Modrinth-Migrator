const MODRINTH_CLIENT_ID = '50zijYLk';

/**
 * Creates a modrinth URI with a given URL encoded callback
 * @param {string | null} curseforgeSlug
 * @param {string | null} modrinthId
 * @returns {string} The callback URI
 */
export const CreateModrinthUri = (curseforgeSlug, modrinthId) => {
  const uri = new URL(`${window.location.origin}${window.location.pathname}`);
  uri.searchParams.set('curseforgeSlug', curseforgeSlug);
  uri.searchParams.set('modrinthId', modrinthId);
  return `https://modrinth.com/auth/authorize?client_id=${MODRINTH_CLIENT_ID}&redirect_uri=${encodeURIComponent(uri.toString())}&scope=PROJECT_WRITE+VERSION_CREATE`;
};

/**
 * Handles Modrinth's callback after OAuth is completed
 */
export const ModrinthOauthCallbackHandler = () => {
  const params = new URLSearchParams(window.location.search);
  if (!params.has('code')) return null;
  const ret = Object.fromEntries(params);

  if (!Object.keys(ret).length) return null;

  const redirectUri = new URL(`${window.location.origin}${window.location.pathname}`);
  redirectUri.searchParams.set('curseforgeSlug', params.get('curseforgeSlug'));
  redirectUri.searchParams.set('modrinthId', params.get('modrinthId'));

  return { ...ret, redirectUri: redirectUri.toString() };
};
