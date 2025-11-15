# Changelog

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
