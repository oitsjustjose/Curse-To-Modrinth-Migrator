const OAUTH_KEY = 'modrinth-oauth-token';

/**
 * Creates a modrinth URI with a given URL encoded callback
 * @param {string | null} curseforgeSlug
 * @param {string | null} modrinthId
 * @returns {string} The callback URI
 */
const CreateModrinthUri = (curseforgeSlug, modrinthId) => {
  const uri = new URL(`${window.location.origin}${window.location.pathname}`);
  curseforgeSlug && curseforgeSlug.length && uri.searchParams.set('curseforgeSlug', curseforgeSlug);
  modrinthId && curseforgeSlug.length && uri.searchParams.set('modrinthId', modrinthId);
  return `https://modrinth.com/auth/authorize?client_id=50zijYLk&redirect_uri=${encodeURIComponent(uri.toString())}&scope=PROJECT_WRITE+VERSION_CREATE`;
};

export const GetModrinthOauth = () => window.localStorage.getItem(OAUTH_KEY);

/**
 *
 * @param {string | null} curseforgeSlug
 * @param {string | null} modrinthId
 * @returns
 */
export const DoModrinthOauth = (curseforgeSlug, modrinthId) => {
  const uri = CreateModrinthUri(curseforgeSlug, modrinthId);
  window.location.href = uri;
};

/**
 * Handles Modrinth's callback after OAuth is completed
 */
export const ModrinthOauthCallbackHandler = () => {
  const params = new URLSearchParams(window.location.search);
  if (!params.has('code')) return null;

  window.localStorage.setItem(OAUTH_KEY, params.get('code'));
  params.delete('code');

  const ret = Object.fromEntries(params);
  return Object.keys(ret).length ? ret : null;
};
