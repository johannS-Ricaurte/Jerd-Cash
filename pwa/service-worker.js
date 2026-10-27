// Versión de caché
const CACHE_NAME = "jerd-cash-public-v4";

// Recursos públicos necesarios
const HOME_URL = "/";
const OFFLINE_URL = "/offline/";
const SIMULADOR_JS = "/static/js/simulador-home.js";
const TAILWIND_CSS = "/static/css/tailwind-home.css";

// Instalar y guardar los recursos públicos
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll([
                HOME_URL,
                OFFLINE_URL,
                SIMULADOR_JS,
                TAILWIND_CSS
            ]);
        })
    );

    self.skipWaiting();
});

// Activar y eliminar cachés anteriores
self.addEventListener("activate", (event) => {
    event.waitUntil(
        (async () => {
            const nombres = await caches.keys();

            await Promise.all(
                nombres
                    .filter((nombre) =>
                        nombre.startsWith("jerd-cash-public-") &&
                        nombre !== CACHE_NAME
                    )
                    .map((nombre) => caches.delete(nombre))
            );

            await self.clients.claim();
        })()
    );
});

// Interceptar solicitudes
self.addEventListener("fetch", (event) => {
    const request = event.request;

    // Nunca interceptar POST ni otros métodos
    if (request.method !== "GET") return;

    const url = new URL(request.url);

    // No interceptar recursos externos
    if (url.origin !== self.location.origin) return;

    // =====================================
    // HOME PÚBLICO - CACHE FIRST
    // =====================================
    if (request.mode === "navigate" && url.pathname === "/") {

        event.respondWith(
            (async () => {

                const cache = await caches.open(CACHE_NAME);

                // Primero intentar cargar el Home guardado.
                const homeGuardado = await cache.match(HOME_URL);

                if (homeGuardado) {
                    return homeGuardado;
                }

                // Si no está guardado, intentar obtenerlo de Django.
                try {
                    const respuesta = await fetch(request);

                    if (respuesta.ok) {
                        await cache.put(
                            HOME_URL,
                            respuesta.clone()
                        );
                    }

                    return respuesta;

                } catch (error) {

                    return (
                        await cache.match(OFFLINE_URL) ||
                        Response.error()
                    );
                }

            })()
        );

        return;
    }
    // =====================================
    // JAVASCRIPT DEL SIMULADOR
    // =====================================
    if (
        url.pathname === SIMULADOR_JS ||
        url.pathname === TAILWIND_CSS
    ) {
        event.respondWith(
            (async () => {
                const cache = await caches.open(CACHE_NAME);

                try {
                    const respuesta = await fetch(request);

                    if (respuesta.ok) {
                        await cache.put(request, respuesta.clone());
                    }

                    return respuesta;
                } catch (error) {
                    return (
                        await cache.match(request) ||
                        Response.error()
                    );
                }
            })()
        );

        return;
    }

    // =====================================
    // OTRAS PÁGINAS
    // =====================================
    if (request.mode === "navigate") {
        event.respondWith(
            (async () => {
                try {
                    return await fetch(request);
                } catch (error) {
                    const cache = await caches.open(CACHE_NAME);

                    return (
                        await cache.match(OFFLINE_URL) ||
                        Response.error()
                    );
                }
            })()
        );
    }
});