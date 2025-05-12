// Basic Edge Function
export const handler = async (req: Request) => {
  return new Response(JSON.stringify({ message: "Hello from Edge Functions!" }), {
    headers: { "Content-Type": "application/json" }
  });
};
