# Changelog

## [0.4.1](https://github.com/athrael-soju/Snappy/compare/v0.4.0...v0.4.1) (2025-12-15)


### Features

* add deepseek timeout argument to command line interface and update default timeout in configuration ([792db2e](https://github.com/athrael-soju/Snappy/commit/792db2ed389f285e6222992b9f914bdc42e96ca4))
* add DuckDB badge to README for analytics support ([89ccb7d](https://github.com/athrael-soju/Snappy/commit/89ccb7d97aa59784d900aa72f00ba02dedf619f7))
* add initial paper.tex and README.json files for document retrieval project ([f9ab6c3](https://github.com/athrael-soju/Snappy/commit/f9ab6c3f8783bae8d2380b96ff9e282aede232b3))
* add max_workers argument for parallel processing in benchmark and OCR endpoints ([6ff5678](https://github.com/athrael-soju/Snappy/commit/6ff567823f596a8bfd8979564ef3f266ca529655))
* add performance evaluation figures and token savings analysis to paper.tex ([0365dfc](https://github.com/athrael-soju/Snappy/commit/0365dfc505c6b126bb95ee693692590979b064c4))
* add script to generate comparative benchmark charts for the paper ([db78acd](https://github.com/athrael-soju/Snappy/commit/db78acde4ac4814a0dc76771559ef6f16aa5c667))
* add support for local Tomoro ColQwen embedding models and environment configuration ([2bd70be](https://github.com/athrael-soju/Snappy/commit/2bd70be464e321d405f8489e1cf837012d41b378))
* update figures in paper; replace category performance chart and add new token comparison and radar charts ([4d0acba](https://github.com/athrael-soju/Snappy/commit/4d0acba5fa350fc7e58c2cf592a90ac4b425ac40))
* update paper.tex for clarity and precision; refine model descriptions and improve token efficiency analysis ([9c2b32e](https://github.com/athrael-soju/Snappy/commit/9c2b32ec5703536fbda67f1ef746deb05d5df5f2))
* update performance metrics and token savings in paper.tex; add new figures for category performance and token savings ([ac0e2cf](https://github.com/athrael-soju/Snappy/commit/ac0e2cf2618df54daf03e00ca72113f470271176))
* update README and documentation with patch-to-region relevance propagation details; add new logo images ([6a07e36](https://github.com/athrael-soju/Snappy/commit/6a07e3671e66aac8e1bc1b2eded3f1cd3c03e1f1))
* update version to 0.4.0 across manifest and package files ([82a4451](https://github.com/athrael-soju/Snappy/commit/82a4451a84259cb2f9112b83ba0ef545a484c4d0))


### Bug Fixes

* add error analysis and qualitative examples sections to paper.tex; include heatmap visualizations for improved clarity on model performance ([80e2829](https://github.com/athrael-soju/Snappy/commit/80e282970548081d81f627b0e6a677c8efecf93f))
* correct formatting of numbers and improve clarity in paper sections ([4eef3b1](https://github.com/athrael-soju/Snappy/commit/4eef3b11935d014e457e321a8b04f7ad26a7022c))
* correct similarity map orientation handling in _stack_patch_scores function ([d40c134](https://github.com/athrael-soju/Snappy/commit/d40c1346b723c3b9a6c19e162ed922226f37ee43))
* enhance clarity in paper.tex; refine descriptions of ColPali and its family models ([516ffac](https://github.com/athrael-soju/Snappy/commit/516ffac55f2030bdb15cf43750c7d2c7e5174b14))
* enhance clarity in paper.tex; refine RegionRAG comparison and highlight differences in approach ([a2a747d](https://github.com/athrael-soju/Snappy/commit/a2a747d13c609bec5a42882c55b3370b4b0f73ae))
* enhance clarity in paper.tex; refine Snappy system architecture description and improve query processing details ([4eecf62](https://github.com/athrael-soju/Snappy/commit/4eecf620d70396c945535c7741ff3a5793198288))
* enhance clarity in paper.tex; refine two-stage retrieval architecture description and remove redundant information ([2bcb4df](https://github.com/athrael-soju/Snappy/commit/2bcb4dfffe8c5c26f86fdfc0705b0f2366410223))
* enhance paper.tex by adding visualizations for IoU thresholds, token usage, and category IoU distribution; adjust figure widths for improved clarity ([a70afdb](https://github.com/athrael-soju/Snappy/commit/a70afdba7537c29d6ffc367b04e3078d8abc40fb))
* enhance similarity map handling in _stack_patch_scores function for ColPali and ColQwen formats ([d521423](https://github.com/athrael-soju/Snappy/commit/d5214236179e165ac3fb2f3b693fea0aeb8ee522))
* improve clarity and conciseness in paper.tex; refine model evaluation results and add threshold selection section ([584c133](https://github.com/athrael-soju/Snappy/commit/584c133eaa4f201a0c867ad4a85112afaf303102))
* improve clarity and precision in paper content and formatting ([f18dc8a](https://github.com/athrael-soju/Snappy/commit/f18dc8acfefa4d5981d2d5d745834b8dea448d98))
* improve clarity in paper.tex; refine signal-to-noise ratio discussion and context token savings explanation ([c7f9fb3](https://github.com/athrael-soju/Snappy/commit/c7f9fb3122950d1eca2b8073953887814882c077))
* update abstract and results sections for clarity; refine terminology to emphasize area efficiency metrics ([c44c1ad](https://github.com/athrael-soju/Snappy/commit/c44c1adc69d943f692e0c4ee9af408893389d88c))
* update author name in paper title and author section ([8a7ed94](https://github.com/athrael-soju/Snappy/commit/8a7ed949fd3b4a122f4384d5ff58ce2d5603d6b0))
* update eess metrics in paper.tex to correct IoU values for improved accuracy ([5dac0fd](https://github.com/athrael-soju/Snappy/commit/5dac0fdd15a5935aac8602640e92e5d41cfe946a))
* update IoU box plot sorting to prioritize ColQwen3-4B for consistency with Table 4; replace outdated figure ([865a7d6](https://github.com/athrael-soju/Snappy/commit/865a7d6c09e35232f24f8c74bb9c6d88d9cfbbf2))
* update Next.js and related dependencies to version 16.0.7 ([d48e49b](https://github.com/athrael-soju/Snappy/commit/d48e49b79580ddfc908bc0c1099f7a37d0466572))
* update paper.tex and benchmark scripts for clarity and accuracy; reorder model configurations ([31e97ea](https://github.com/athrael-soju/Snappy/commit/31e97eab27c3e3f6e8a8afa5e010aa37ea945011))
* update paper.tex to clarify the abstract and improve the description of the hybrid architecture; enhance details on evaluation metrics and model configurations ([9614883](https://github.com/athrael-soju/Snappy/commit/96148835edf56febae7b9ab6e1ee0b706340340d))
* update paper.tex to enhance clarity and improve precision and signal-to-noise ratio sections; adjust figure widths for better presentation ([934637a](https://github.com/athrael-soju/Snappy/commit/934637abc0362292b6fd8b4e8cea4d73d41cca74))
* update paper.tex to improve section references and enhance clarity; add cleveref package for better cross-referencing ([2c5388b](https://github.com/athrael-soju/Snappy/commit/2c5388bbd86f4924b1f27ab09c78eacfd5bd9a6d))
* update references and improve clarity in paper.tex; enhance descriptions of ColPali-family models and architectural differences ([a2e3987](https://github.com/athrael-soju/Snappy/commit/a2e39878a2c51ce175badf85a95af9cb81e81071))
* update section references and improve clarity in paper.pdf; refine model evaluation results and threshold selection discussion ([8bb859b](https://github.com/athrael-soju/Snappy/commit/8bb859bc295bff1f9fde4f5c0bc728f305bdb085))
* update theoretical analysis and error analysis sections for clarity; adjust area efficiency metrics and refine localization failure categorization ([d0cd843](https://github.com/athrael-soju/Snappy/commit/d0cd8431f027b1ab837ac328d6639a7981a567b4))


### Code Refactoring

* remove environment type configuration and related comments ([3aa6620](https://github.com/athrael-soju/Snappy/commit/3aa66208cae0ec56c1b9b811ec8d2df34febe4ff))
* remove hit IoU threshold argument from command line interface and related configurations ([91c6fae](https://github.com/athrael-soju/Snappy/commit/91c6fae2592da9af063d07705a87bbe520eba193))

## [0.3.8](https://github.com/athrael-soju/Snappy/compare/v0.3.7...v0.3.8) (2025-11-25)


### Features

* add streaming pipeline ([51960c6](https://github.com/athrael-soju/Snappy/commit/51960c696c9510073382b89360c1e17c5500a2a5))
* add streaming pipeline for 6x faster ingestion ([aa00e8b](https://github.com/athrael-soju/Snappy/commit/aa00e8b3f63a224fa89cd329e96e95be87155a27))
* Implement document indexing pipeline with file upload, validation, and comprehensive error handling. ([5d8be8d](https://github.com/athrael-soju/Snappy/commit/5d8be8d7684ba9905f219b6fee7f5e65aa7a9f6c))
* Implement document search using Qdrant with optional OCR data enrichment from DuckDB or MinIO. ([3334eb3](https://github.com/athrael-soju/Snappy/commit/3334eb3ce7a6db9b80936bca861d6a146532062b))


### Code Refactoring

* make streaming pipeline the default, remove legacy code ([e48a27d](https://github.com/athrael-soju/Snappy/commit/e48a27d566142c7856732b5bbe704ee3b562d7be))

## [0.3.7](https://github.com/athrael-soju/Snappy/compare/v0.3.6...v0.3.7) (2025-11-22)


### Bug Fixes

* make hard-coded config constants accessible via imports ([b12de46](https://github.com/athrael-soju/Snappy/commit/b12de4607c8e66fd4f1493f62c086744594d255f))


### Documentation

* add --build flag notice to all service README deployment sections ([a808755](https://github.com/athrael-soju/Snappy/commit/a8087553c58e4e87c45a5cd7282e4deae84358e6))
* add hardware profile recommendations to configuration guide ([7aea1b2](https://github.com/athrael-soju/Snappy/commit/7aea1b2626abec2d1478af0ce02bd7d738fbef4b))
* Add initial documentation for agents, backend, and deepseek-ocr services. ([f403de6](https://github.com/athrael-soju/Snappy/commit/f403de6aa36478e211c3dff4205cf0d622e97286))
* add Makefile-based deployment with service profiles ([2b52f71](https://github.com/athrael-soju/Snappy/commit/2b52f71efa0c177e8ac2d551c14c625f577bde41))
* fix links in deployment options section of README ([4a42ef6](https://github.com/athrael-soju/Snappy/commit/4a42ef6be8aca6b4e9855a0ca1c1efeb03ca77b2))
* update architecture and analysis docs to reflect auto-enabled features ([35445b6](https://github.com/athrael-soju/Snappy/commit/35445b61042c59b1cd1f99d2d2c617354fbba1f6))
* update configuration help text to reflect unified deployment model ([96dc80c](https://github.com/athrael-soju/Snappy/commit/96dc80cfd9c4098686b3bc61b9f5d084fae78d58))
* update Docker registry workflow and docs to reflect unified ColPali deployment ([f542a6b](https://github.com/athrael-soju/Snappy/commit/f542a6b980c2b1091a19e8e500b432dbbe24a6ef))
* update project description and enhance features in README ([0ab222d](https://github.com/athrael-soju/Snappy/commit/0ab222d85e783a7e350a898a0625bf641011985a))


### Code Refactoring

* disable mean pooling and restore strict error handling in ColPali client ([96be6c2](https://github.com/athrael-soju/Snappy/commit/96be6c2a7988118c19a0b9d10129b73b67339505))
* make mean pooling gracefully degrade when model lacks patch support ([551a565](https://github.com/athrael-soju/Snappy/commit/551a56592e965129192aafd0ba951edb652645c8))
* remove --build flag from Makefile and add graceful degradation for ColPali patch errors ([8a5d418](https://github.com/athrael-soju/Snappy/commit/8a5d41816ea63ba99506f8abb1af063d68d1193c))
* remove auto-config toggle and add profile-based feature flags ([d494c32](https://github.com/athrael-soju/Snappy/commit/d494c329d173160b1d21d3d04eefc437ed6ed13f))
* remove CPU/GPU profiles, default to GPU-first deployment ([5acde60](https://github.com/athrael-soju/Snappy/commit/5acde6035bfd59ed84c447bd9826fe737f4e0c07))
* replace curl with native bash for Qdrant healthchecks ([1e7e84d](https://github.com/athrael-soju/Snappy/commit/1e7e84d085c4fe2b335f6db4d193e3f0198df98a))
* simplify configuration for wider audience ([b3c941b](https://github.com/athrael-soju/Snappy/commit/b3c941ba7ebfc9c13cf78cd164b85c68821e10c6))
* unify ColPali deployment with automatic hardware detection ([0b56c04](https://github.com/athrael-soju/Snappy/commit/0b56c04827b8aff1c72433b9b116dc3273951348))

## [0.3.6](https://github.com/athrael-soju/Snappy/compare/v0.3.5...v0.3.6) (2025-11-15)


### Documentation

* enhance README and architecture documentation for OCR retrieval modes ([924c311](https://github.com/athrael-soju/Snappy/commit/924c3118b2f28ca31e9b0e563aed3410a277e2d8))


### Code Refactoring

* enhance chat service to support OCR and region images confi… ([c54353d](https://github.com/athrael-soju/Snappy/commit/c54353d7b67eeb1000e6f80b21e4376307cc53c4))
* enhance chat service to support OCR and region images configuration ([07cd09c](https://github.com/athrael-soju/Snappy/commit/07cd09cb56170d38a5ba670e6de5a737b9c060bb))
* improve styling and accessibility in MarkdownRenderer component ([9681596](https://github.com/athrael-soju/Snappy/commit/9681596f0b15f6310b3dd42d22d5316dc90dfbe3))

## [0.3.1](https://github.com/athrael-soju/Snappy/compare/v0.3.0...v0.3.1) (2025-11-13)


### Features

* add method to strip block comments from SQL queries and enforce query length limit ([320a08c](https://github.com/athrael-soju/Snappy/commit/320a08ca956e909dd3aec3a9cf907d7dc6b5579e))
* enhance DuckDBManager close method with checkpointing and improve entrypoint script for graceful shutdown ([d9280dc](https://github.com/athrael-soju/Snappy/commit/d9280dc93beacd58624151f6867cd33ecd25b1d9))
* enhance OCR processing with batch handling and adjustable worker settings ([dbe4fa6](https://github.com/athrael-soju/Snappy/commit/dbe4fa6e6becfcea469bc8bd8709ca630bbad8eb))
* handle duplicate document uploads and provide user feedback ([0ad663e](https://github.com/athrael-soju/Snappy/commit/0ad663e57b768b128031a968b9c9fefba4401af8))
* implement document deduplication and metadata storage in DuckDB ([6cf66a8](https://github.com/athrael-soju/Snappy/commit/6cf66a8e9ce6c8796f6f3c0b68e96426898fc07b))
* implement thread-safe error tracking for service initialization and enhance error handling in various services ([5562949](https://github.com/athrael-soju/Snappy/commit/5562949e00d56735b5c4d300b5c91fed1845df1d))
* implement UUID-based naming for OCR results and enhance storage structure ([8de816e](https://github.com/athrael-soju/Snappy/commit/8de816e95bd1b2f70cf896d83bc5278857908609))
* update environment variables and improve security measures ([e4b8cd7](https://github.com/athrael-soju/Snappy/commit/e4b8cd7ae0a758bac36cbb417ce4581283b18970))

## [0.2.1](https://github.com/athrael-soju/Snappy/compare/v0.2.0...v0.2.1) (2025-11-06)


### Features

* enhance architecture documentation with DeepSeek OCR integration and update request flows ([70e41f2](https://github.com/athrael-soju/Snappy/commit/70e41f2c404110a9f238ef979bef6a15305e9841))
* implement centralized logging system across the frontend ([5cf641b](https://github.com/athrael-soju/Snappy/commit/5cf641b146cf8360c8d8fc8b20cbadb97cadadbd))
* implement centralized logging system across the frontend ([95d5974](https://github.com/athrael-soju/Snappy/commit/95d5974c62ba31c4e60d6c1c91c6f21e7a79546d))
* refine descriptions in documentation for clarity and precision ([91a94d2](https://github.com/athrael-soju/Snappy/commit/91a94d2bf666d55a0ec93b1a33bd59f338ecb8e6))
* update Dockerfile and application logging for DeepSeek OCR serv… ([de88a95](https://github.com/athrael-soju/Snappy/commit/de88a95e74cd5b16493a1526f456053d91d402bd))
* update Dockerfile and application logging for DeepSeek OCR service startup ([b905693](https://github.com/athrael-soju/Snappy/commit/b905693407d3b5362ae05a1dd36cda47c849b802))
* update documentation and restructure state management architect… ([d27019a](https://github.com/athrael-soju/Snappy/commit/d27019af67fa7d83fb3f887cfcf0b757e758d4f6))
* update documentation and restructure state management architecture in frontend ([5f90fdd](https://github.com/athrael-soju/Snappy/commit/5f90fdd00aceaf97e78d2517729de6b874007523))


### Bug Fixes

* clarify DeepSeek OCR integration details in README ([afc8796](https://github.com/athrael-soju/Snappy/commit/afc879646c1906beeae088967c8b68ea70175e4a))

## [0.1.3](https://github.com/athrael-soju/Snappy/compare/0.1.2...v0.1.3) (2025-10-23)


### Features

* add comprehensive documentation for Docker images and workflows ([0aa9b24](https://github.com/athrael-soju/Snappy/commit/0aa9b244b5412fb79dedf5844b60a612a6e8b1cf))
* add configuration persistence and version retrieval endpoints ([f865219](https://github.com/athrael-soju/Snappy/commit/f8652191e3fd6dccaf6285bd07e3eeb8208e927e))
* add configuration persistence and version retrieval endpoints ([587c28d](https://github.com/athrael-soju/Snappy/commit/587c28d20e1abcc476878d1f6ecb28df187939b8))
* add contributing guide to enhance community involvement ([6e18b54](https://github.com/athrael-soju/Snappy/commit/6e18b54e7e476ef8dc103dfece17b5732fd49cdf))
* add security policy document to outline security practices and reporting procedures ([a3a43d2](https://github.com/athrael-soju/Snappy/commit/a3a43d2435c6786051bb6f49f7fc3fe680e43608))
* add snappy_dark_resized image for improved UI ([f14640d](https://github.com/athrael-soju/Snappy/commit/f14640d5e84c6a9f6ec3b62911ed88f965cd7028))
* add use cases section to README and create social preview HTML files for light and dark modes; update package.json with additional keywords ([41c1610](https://github.com/athrael-soju/Snappy/commit/41c1610a71d4ffbbdb705394d98ca4a9a1e98ccc))
* enhance configuration UI with real-time validation, draft detection, and improved reset options ([a33a61b](https://github.com/athrael-soju/Snappy/commit/a33a61be5afd1e484da81335148d1e6145eb76e7))
* enhance README with project stats and tech stack badges ([1ef910c](https://github.com/athrael-soju/Snappy/commit/1ef910c09477176b124b20cf0116d4fc99735330))
* trigger system status change event on upload completion ([e07fbc5](https://github.com/athrael-soju/Snappy/commit/e07fbc57eaeaaee67f8bc9b61a3f598998b899b2))
* trigger system status change event on upload completion ([d96424a](https://github.com/athrael-soju/Snappy/commit/d96424a19d4618ba283c5895a051ba3669c77ac6))
* update NextTopLoader styling with gradient backgrounds and enab… ([1163cb7](https://github.com/athrael-soju/Snappy/commit/1163cb7ade773bf26fd11951b6cd705920b4e4dd))
* update NextTopLoader styling with gradient backgrounds and enable spinner ([1e57986](https://github.com/athrael-soju/Snappy/commit/1e5798663cad2909b1cabfbdfc5c814bedb7bb97))


### Bug Fixes

* rename base stage to deps in Dockerfile for clarity ([69c0c67](https://github.com/athrael-soju/Snappy/commit/69c0c671b82e0acf0fd32a43b0bf1c5c123e8d61))


### Code Refactoring

* implement lazy initialization for OpenAI client to optimize resource usage ([d2aa62c](https://github.com/athrael-soju/Snappy/commit/d2aa62c634d9aff39b685ea3b4bc1a9950e8aaa8))
* remove branch trigger for main in Docker publish workflow ([632c054](https://github.com/athrael-soju/Snappy/commit/632c0549a6439520976b6ee7e63acdeb571139c2))
* remove persist configuration functionality and related UI components ([9420e61](https://github.com/athrael-soju/Snappy/commit/9420e61dcb550b7b668a3dbe4e802b1a53d5917d))
* remove Resizable component and its related files ([a0a53ad](https://github.com/athrael-soju/Snappy/commit/a0a53ad6ae821f4b98d8967bc677ef7c2175878f))
* remove unused Snappy image file ([51577bb](https://github.com/athrael-soju/Snappy/commit/51577bb1e9ea0210477dd260cf9f29dc41d766a1))
* remove unused UI components including context menu, drawer, form, input OTP, menubar, navigation menu, toggle group, and toggle; update package dependencies ([9df0b22](https://github.com/athrael-soju/Snappy/commit/9df0b22ee77c159b617954cc9d8a0d28a0293386))
* update Docker build platforms to only include linux/amd64 ([3299f84](https://github.com/athrael-soju/Snappy/commit/3299f84cb578c9ae10de3854a6043edcf530d131))
