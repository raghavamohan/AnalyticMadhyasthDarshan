export default {
  fetch() {
    return new Response("google-site-verification: google8e0758eaee6de8ab.html\n", {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "public, max-age=3600",
      },
    });
  },
};
