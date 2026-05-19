export default function APIsPage() {
  return (
    <div className="p-8">
      <div className="label-caps mb-2">APIs</div>
      <h1 className="font-display text-5xl font-black leading-none m-0">
        API Providers
      </h1>
      <p className="mt-3 text-zinc-600 max-w-3xl">
        This page is where you manage external providers like Groq, OpenAI,
        Anthropic, Together, Apify, and Hunter.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-8">
        <div className="bg-white brutal-border p-5">
          <div className="font-display text-2xl font-bold mb-2">LLM Models</div>
          <div className="text-sm text-zinc-600">
            Configured through backend .env and pathway LLM controls.
          </div>
        </div>

        <div className="bg-white brutal-border p-5">
          <div className="font-display text-2xl font-bold mb-2">Apify</div>
          <div className="text-sm text-zinc-600">
            Used for real job scraping when job_provider is set to apify.
          </div>
        </div>

        <div className="bg-white brutal-border p-5">
          <div className="font-display text-2xl font-bold mb-2">Hunter</div>
          <div className="text-sm text-zinc-600">
            Used for external contact discovery when enabled.
          </div>
        </div>
      </div>
    </div>
  );
}