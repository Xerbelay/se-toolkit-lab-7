# Bot Development Plan

This bot will be implemented incrementally so that each task adds a clear layer of functionality without breaking the previous one. The first step is to scaffold a clean bot structure inside `bot/` with an entry point, configuration loading, a handler directory, and a CLI `--test` mode. The handlers will be plain Python functions that return text and do not depend on Telegram classes. This makes them reusable from the command line, from tests, and from Telegram.

The second step is backend integration. Service modules will be added to call the LMS API for health checks, lab listings, and score queries. Command handlers will use those services and format readable responses for users. Errors from the backend will be handled gracefully.

The third step is intent routing for natural language messages. Free-form user input will be mapped to the same internal handlers using an LLM or classifier layer with safe fallbacks.

The final step is deployment and verification on the VM, including `.env.bot.secret`, process startup, logging, and Telegram testing.
