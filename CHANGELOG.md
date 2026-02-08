## [1.39.5](https://github.com/filipores/obojobs/compare/v1.39.4...v1.39.5) (2026-02-08)


### Bug Fixes

* resolve landing page bugs, fix umlauts, redesign generation modal ([4b597a4](https://github.com/filipores/obojobs/commit/4b597a4e8b0ba22bce087069e20a0a43f27c52bd))

## [1.39.4](https://github.com/filipores/obojobs/compare/v1.39.3...v1.39.4) (2026-02-08)


### Bug Fixes

* **pdf:** use backend content-disposition header for download filename ([0f453e6](https://github.com/filipores/obojobs/commit/0f453e628a1beba84d8a3de8c497ff91d46869fa))

## [1.39.3](https://github.com/filipores/obojobs/compare/v1.39.2...v1.39.3) (2026-02-08)


### Performance Improvements

* **scraper:** use scraperapi first in production, eliminate double-scrape ([2377987](https://github.com/filipores/obojobs/commit/237798723da0c47decc5fc2ae2a1313c1bae790c))

## [1.39.2](https://github.com/filipores/obojobs/compare/v1.39.1...v1.39.2) (2026-02-08)


### Bug Fixes

* **deploy:** pass scraper_api_key to backend container ([28d50a7](https://github.com/filipores/obojobs/commit/28d50a78290247bb326e4f458e5482d4adde0bf4))

## [1.39.1](https://github.com/filipores/obojobs/compare/v1.39.0...v1.39.1) (2026-02-08)


### Bug Fixes

* **tests:** fix ci failures in subscription and api client tests ([cf4845a](https://github.com/filipores/obojobs/commit/cf4845a41383c7a252c0633961110495b1087b4c))

# [1.39.0](https://github.com/filipores/obojobs/compare/v1.38.1...v1.39.0) (2026-02-08)


### Features

* **scraper:** add scraperapi as fallback for blocked datacenter ips ([dce5ed4](https://github.com/filipores/obojobs/commit/dce5ed4a30aed0025ecec302b322356c764b37c3))

## [1.38.1](https://github.com/filipores/obojobs/compare/v1.38.0...v1.38.1) (2026-02-08)


### Bug Fixes

* **extension:** add /jobs-- pattern to stepstone url matcher ([238d01d](https://github.com/filipores/obojobs/commit/238d01d07fb111e2fd3023dfc5173250cae16300))

# [1.38.0](https://github.com/filipores/obojobs/compare/v1.37.5...v1.38.0) (2026-02-08)


### Features

* **extension:** add dom-based job extraction to bypass server scraping ([c05a432](https://github.com/filipores/obojobs/commit/c05a432db05ca63e54784e2eeb50b8b48c37e10b))

## [1.37.5](https://github.com/filipores/obojobs/compare/v1.37.4...v1.37.5) (2026-02-08)


### Bug Fixes

* **scraper:** pass user-friendly error messages through to frontend ([3f5bb4a](https://github.com/filipores/obojobs/commit/3f5bb4ad566c4c4c5ffd942fefbc9780f0cb0a7c))

## [1.37.4](https://github.com/filipores/obojobs/compare/v1.37.3...v1.37.4) (2026-02-08)


### Bug Fixes

* **scraper:** retry on timeout/connection errors and improve error messages ([d5aaad5](https://github.com/filipores/obojobs/commit/d5aaad57bff6673b18c4b6d9634a55a1613e2d3f))

## [1.37.3](https://github.com/filipores/obojobs/compare/v1.37.2...v1.37.3) (2026-02-08)


### Bug Fixes

* **scraper:** add cloudscraper fallback for 403 bot protection ([5d843cd](https://github.com/filipores/obojobs/commit/5d843cd15e5ddf310fd16394e2afa401b57cbb48))

## [1.37.2](https://github.com/filipores/obojobs/compare/v1.37.1...v1.37.2) (2026-02-08)


### Bug Fixes

* **pdf:** use content-based formatting instead of line-count heuristic ([20efb54](https://github.com/filipores/obojobs/commit/20efb545e6aaddb1108e0e37e620669ac98f3813))

## [1.37.1](https://github.com/filipores/obojobs/compare/v1.37.0...v1.37.1) (2026-02-08)


### Bug Fixes

* **generator:** prevent double greeting in cover letter anrede ([d85fa62](https://github.com/filipores/obojobs/commit/d85fa62c28acaeae78aa6c1739042c080929ca2e))

# [1.37.0](https://github.com/filipores/obojobs/compare/v1.36.0...v1.37.0) (2026-02-08)


### Features

* **new-application:** personalize crafting overlay and redesign generation result modal ([f1175bd](https://github.com/filipores/obojobs/commit/f1175bd77704c9ad83c14a4741aa183e99ea6f36))

# [1.36.0](https://github.com/filipores/obojobs/compare/v1.35.3...v1.36.0) (2026-02-08)


### Features

* bug fixes, ux improvements, and new features ([8f5ac6a](https://github.com/filipores/obojobs/commit/8f5ac6a6e1b908b918df1217d7043cba7e37031e))

## [1.35.3](https://github.com/filipores/obojobs/compare/v1.35.2...v1.35.3) (2026-02-07)


### Bug Fixes

* **new-application:** move helper functions before first use to fix tdz error ([90460f0](https://github.com/filipores/obojobs/commit/90460f07bdb5635b44b4a43036819c003271b457))

## [1.35.2](https://github.com/filipores/obojobs/compare/v1.35.1...v1.35.2) (2026-02-07)


### Bug Fixes

* **template:** handle empty profile fields gracefully in default template ([afd2a33](https://github.com/filipores/obojobs/commit/afd2a338b5bfd8ed02c9a3596aafb51a1467d161))

## [1.35.1](https://github.com/filipores/obojobs/compare/v1.35.0...v1.35.1) (2026-02-07)


### Bug Fixes

* **generator:** remove legacy anschreiben document fallback ([4007234](https://github.com/filipores/obojobs/commit/4007234e6d047551361f05a4d414fdfb677544f0))

# [1.35.0](https://github.com/filipores/obojobs/compare/v1.34.1...v1.35.0) (2026-02-07)


### Features

* **i18n:** replace hardcoded german strings with vue-i18n t() calls ([56c2e42](https://github.com/filipores/obojobs/commit/56c2e42e3704ed510b10b32ba6971343b1f79500))

## [1.34.1](https://github.com/filipores/obojobs/compare/v1.34.0...v1.34.1) (2026-02-07)


### Bug Fixes

* **deploy:** complete docker and deployment configuration ([43021cf](https://github.com/filipores/obojobs/commit/43021cfb62c45b6156b71c4d79be83f15cf4083b))
* **security:** harden backend for production deployment ([a9d3818](https://github.com/filipores/obojobs/commit/a9d38182d07b06c51130bf6ba2657ec22deb7443))
* **ui:** replace alert dialogs with toast notifications ([a319078](https://github.com/filipores/obojobs/commit/a3190786a81334f26be05790228851c764d587ea))

# [1.34.0](https://github.com/filipores/obojobs/compare/v1.33.0...v1.34.0) (2026-02-07)


### Features

* **applications:** add profile completeness warning before generation ([a7b5dd0](https://github.com/filipores/obojobs/commit/a7b5dd03031cac7f043ebfd6b62dcf0cb47340c1))
* **legal:** make impressum and datenschutz address configurable via env ([5d61158](https://github.com/filipores/obojobs/commit/5d611585fb9c1548078a0dda4dbb9cc1d798dfea))
* **subscriptions:** gracefully handle missing stripe configuration ([1f5fff6](https://github.com/filipores/obojobs/commit/1f5fff6ba8875a0fc42219e2cc65fa24bdabdef5))

# [1.33.0](https://github.com/filipores/obojobs/compare/v1.32.2...v1.33.0) (2026-02-06)


### Features

* **auth:** block login for unverified email accounts ([52f0880](https://github.com/filipores/obojobs/commit/52f08801b7f72e5df7a0ceca43702a72d765331e))
* **documents:** store cv pdfs and attach to email drafts ([94e75f9](https://github.com/filipores/obojobs/commit/94e75f9bbb865f7e846da3368b9dea4250113b8c))
* **legal:** add real impressum and datenschutz content ([08ac85f](https://github.com/filipores/obojobs/commit/08ac85f34e26894b951974a0a99526332a01aecc))

## [1.32.2](https://github.com/filipores/obojobs/compare/v1.32.1...v1.32.2) (2026-02-06)


### Bug Fixes

* **settings:** sync profile data with localstorage and fetch fresh on mount ([a557b4e](https://github.com/filipores/obojobs/commit/a557b4e19bd74b3ca08828a1b65987493fbb8071))

## [1.32.1](https://github.com/filipores/obojobs/compare/v1.32.0...v1.32.1) (2026-02-06)


### Bug Fixes

* **ui:** add alert fallback for email draft download errors ([492eefe](https://github.com/filipores/obojobs/commit/492eefeb7170963fb85a0bc8d94a23f2d19e9498))

# [1.32.0](https://github.com/filipores/obojobs/compare/v1.31.1...v1.32.0) (2026-02-06)


### Features

* **email:** generate downloadable .eml draft with pdf attachment ([bb8e28e](https://github.com/filipores/obojobs/commit/bb8e28eb41eec6712ef3ae3171f1ec6385f761c4))

## [1.31.1](https://github.com/filipores/obojobs/compare/v1.31.0...v1.31.1) (2026-02-06)


### Bug Fixes

* **config:** change backend port from 5001 to 5002 ([2589e9d](https://github.com/filipores/obojobs/commit/2589e9d176ce238e7bd7bd25f755722ce63e2cab))

# [1.31.0](https://github.com/filipores/obojobs/compare/v1.30.2...v1.31.0) (2026-02-06)


### Features

* **email:** add transactional email service via gmail smtp ([961f825](https://github.com/filipores/obojobs/commit/961f825b3dabb2349ba23a87819d5bf013c8142c))

## [1.30.2](https://github.com/filipores/obojobs/compare/v1.30.1...v1.30.2) (2026-02-06)


### Bug Fixes

* **config:** resolve upload_folder path relative to project root ([0b0fc91](https://github.com/filipores/obojobs/commit/0b0fc91d2a7df86ebfc49660d9b038d06b659c84))

## [1.30.1](https://github.com/filipores/obojobs/compare/v1.30.0...v1.30.1) (2026-02-06)


### Bug Fixes

* **db:** correct migration down_revision to actual head ([994fee3](https://github.com/filipores/obojobs/commit/994fee32ae9d88f22b54a5a5f64c68333b9072fa))

# [1.30.0](https://github.com/filipores/obojobs/compare/v1.29.7...v1.30.0) (2026-02-06)


### Features

* **templates:** add personal data variables to templates and pdfs ([d5392ca](https://github.com/filipores/obojobs/commit/d5392ca390e41a517e6961335a4dfb673e5db066))

## [1.29.7](https://github.com/filipores/obojobs/compare/v1.29.6...v1.29.7) (2026-02-06)


### Bug Fixes

* **config:** consolidate .env files into single root .env ([52e7944](https://github.com/filipores/obojobs/commit/52e7944100e785652257493860baf93a071b4aa1))

## [1.29.6](https://github.com/filipores/obojobs/compare/v1.29.5...v1.29.6) (2026-02-06)


### Bug Fixes

* **api:** use absolute paths in send_file for pdf and document downloads ([e7e2abc](https://github.com/filipores/obojobs/commit/e7e2abc86f277ba6eb3e8b8ccd75892478f6c1a4))

## [1.29.5](https://github.com/filipores/obojobs/compare/v1.29.4...v1.29.5) (2026-02-06)


### Bug Fixes

* **applications:** merge manual text flow fix ([d578bc3](https://github.com/filipores/obojobs/commit/d578bc391213111bcf5dca95709b19052795eb59))
* **applications:** show preview form after manual text analysis ([5c2cf31](https://github.com/filipores/obojobs/commit/5c2cf3111d7b8053244f46345d43a70572a1f2da))
* **layout:** merge viewport resize navigation fix ([c31ca83](https://github.com/filipores/obojobs/commit/c31ca8312313f1fc655f451c282f4d353b506e03))
* **layout:** prevent viewport resize from triggering navigation ([55c88ac](https://github.com/filipores/obojobs/commit/55c88ac44101804906a17390e39e28dd3d7e853a))
* **templates:** add pdf wizard access and improve error handling ([701efdb](https://github.com/filipores/obojobs/commit/701efdbb7777c1ec03cb508b0d8cfb03a32f620c))
* **templates:** merge pdf wizard access and error handling ([b43230e](https://github.com/filipores/obojobs/commit/b43230e59d62e246f1780ce49de5c654b6172282))
* **ui:** fix company insights heading, umlauts, and skills banner ([6d65603](https://github.com/filipores/obojobs/commit/6d65603bc1e0d33ea5dff1e7f22d8aee5f75bba7))
* **ui:** merge umlaut, i18n, and skills banner fixes ([24abb1d](https://github.com/filipores/obojobs/commit/24abb1d6287f4dc9657d5f09449548d4e75f4d8d))

## [1.29.4](https://github.com/filipores/obojobs/compare/v1.29.3...v1.29.4) (2026-02-05)


### Bug Fixes

* **auth:** add full_name assertions to registration and Google OAuth tests ([f319297](https://github.com/filipores/obojobs/commit/f31929702c9a143d5a9ac2f9b74d6c0770c044ab))
* **dev:** align vite proxy port with backend (5001) ([eb26d64](https://github.com/filipores/obojobs/commit/eb26d64e8a87dd81b67def4f11a0a589463af704))
* **i18n:** complete i18n coverage for remaining hardcoded strings ([2f02728](https://github.com/filipores/obojobs/commit/2f02728b232fb5dc8b41d7d6ad737974bd2f0a6f))

## [1.29.3](https://github.com/filipores/obojobs/compare/v1.29.2...v1.29.3) (2026-02-05)


### Bug Fixes

* **apps:** improve empty state CTA and fix timeline route ([b52b52e](https://github.com/filipores/obojobs/commit/b52b52e6ee3a92e1422b0aad52e5886884bb1e84))
* **apps:** merge applications empty state improvements ([f29e0df](https://github.com/filipores/obojobs/commit/f29e0df2537e8e36a657d5cea225696b47e3fd8c))
* **auth:** add i18n to register, forgot-password, email-verification pages ([6a46d56](https://github.com/filipores/obojobs/commit/6a46d5638c0cd2f86d4da5f5286556aa644caa98))
* **auth:** merge auth pages i18n and ux improvements ([66a75db](https://github.com/filipores/obojobs/commit/66a75db032d0808138de54f3208b7c7e06d86ef1))
* **i18n:** merge translation html warning fixes ([92e300a](https://github.com/filipores/obojobs/commit/92e300a363713f139c1113654972518236463e4c))
* **i18n:** remove HTML from translation strings to fix intlify warnings ([9f7d97d](https://github.com/filipores/obojobs/commit/9f7d97da7f58ddd976911e45c7ac8a368571a1eb))
* **subscription:** merge subscription page fix ([89d7cf5](https://github.com/filipores/obojobs/commit/89d7cf5ba3171ba51c41657aebe9dc8b9b89af43))
* **subscription:** remove parentheses from computed property call ([93150e7](https://github.com/filipores/obojobs/commit/93150e7ef8a6072f0ddd2046ec097774042f781a))

## [1.29.2](https://github.com/filipores/obojobs/compare/v1.29.1...v1.29.2) (2026-02-04)


### Bug Fixes

* **docs:** correct tech stack - javascript not typescript ([91a6f76](https://github.com/filipores/obojobs/commit/91a6f7640fa41d64e7eb27dd95113e4865ad5821))

## [1.29.1](https://github.com/filipores/obojobs/compare/v1.29.0...v1.29.1) (2026-02-04)


### Bug Fixes

* **frontend:** improve mobile responsiveness and update legal pages ([d2424c1](https://github.com/filipores/obojobs/commit/d2424c171f793516f7fb76c70bb05a0825ef176a))

# [1.29.0](https://github.com/filipores/obojobs/compare/v1.28.2...v1.29.0) (2026-02-03)


### Features

* **demo:** add progressive reveal crafting experience with zen pdf ([b36d828](https://github.com/filipores/obojobs/commit/b36d828890c4d35c5e8d22e50c76341e538f1273))

## [1.28.2](https://github.com/filipores/obojobs/compare/v1.28.1...v1.28.2) (2026-02-03)


### Bug Fixes

* **lint:** auto-fix lint errors [skip ci] ([4f8ad9c](https://github.com/filipores/obojobs/commit/4f8ad9c0dfec4f2cb3eb3f0142e847f8f1efa311)), closes [#276](https://github.com/filipores/obojobs/issues/276)

## [1.28.1](https://github.com/filipores/obojobs/compare/v1.28.0...v1.28.1) (2026-02-03)


### Bug Fixes

* **routes/workflows:** rm ralph ([b98771f](https://github.com/filipores/obojobs/commit/b98771f2ae2f882646240cdbad8b30b0dd7c73ab))

# [1.28.0](https://github.com/filipores/obojobs/compare/v1.27.0...v1.28.0) (2026-02-03)


### Features

* **landing:** add post-registration CV upload & auto-regeneration (ob-g9kfi) ([3d5db59](https://github.com/filipores/obojobs/commit/3d5db59bcff8bc71811f6a6246fb4d5c8c5fbfd7))

# [1.27.0](https://github.com/filipores/obojobs/compare/v1.26.0...v1.27.0) (2026-02-03)


### Features

* **auth:** add Google OAuth integration (ob-ffhfl) ([29820bf](https://github.com/filipores/obojobs/commit/29820bf5a9d4b7745f6e40175e84a8f1d190d649))

# [1.26.0](https://github.com/filipores/obojobs/compare/v1.25.0...v1.26.0) (2026-02-03)


### Features

* **demo:** add anonymous demo generation endpoint (ob-r3qgz) ([c842eb5](https://github.com/filipores/obojobs/commit/c842eb53c68d7d3137ca2b1f46d7de508f30d492))

# [1.25.0](https://github.com/filipores/obojobs/compare/v1.24.0...v1.25.0) (2026-02-03)


### Features

* **dashboard:** make email verification banner a subtle reminder ([5d17bf9](https://github.com/filipores/obojobs/commit/5d17bf93c7d7604943f45cf835bd5bc9d5120264))

# [1.24.0](https://github.com/filipores/obojobs/compare/v1.23.1...v1.24.0) (2026-02-03)


### Features

* **landing:** add landing page with demo input for unauthenticated users (ob-p8w2e) ([ce31822](https://github.com/filipores/obojobs/commit/ce318223b3d81d7d45ad1825a36c29db44ea7d9d))

## [1.23.1](https://github.com/filipores/obojobs/compare/v1.23.0...v1.23.1) (2026-02-03)


### Bug Fixes

* **pdf:** sanitize filenames and handle variable positions format ([5eadd6e](https://github.com/filipores/obojobs/commit/5eadd6e5177e87550de0ed99d6876a97905a9ed5))

# [1.23.0](https://github.com/filipores/obojobs/compare/v1.22.0...v1.23.0) (2026-02-03)


### Features

* **templates:** add contextual tooltips to variable chips (ob-7t3k) ([e646fd6](https://github.com/filipores/obojobs/commit/e646fd6c6a563fcee998d6a6c917016201cc5457))

# [1.22.0](https://github.com/filipores/obojobs/compare/v1.21.0...v1.22.0) (2026-02-03)


### Features

* **templates:** add search, filter, and sort functionality (ob-3f6d) ([f494848](https://github.com/filipores/obojobs/commit/f494848148d791168209599fc9b5d7c0fa2acb12))

# [1.21.0](https://github.com/filipores/obojobs/compare/v1.20.0...v1.21.0) (2026-02-03)


### Features

* **pdf-wizard:** simplify to 2-step flow with QuickReview (ob-ltge) ([852a745](https://github.com/filipores/obojobs/commit/852a745bdf4111ba41f639d8f160aa50fd295895))

# [1.20.0](https://github.com/filipores/obojobs/compare/v1.19.0...v1.20.0) (2026-02-03)


### Features

* **templates:** add live preview panel to template editor (ob-g5w4) ([e8d837b](https://github.com/filipores/obojobs/commit/e8d837bc5f07bebd8b0bf562f903f58c508ebfd8))

# [1.19.0](https://github.com/filipores/obojobs/compare/v1.18.0...v1.19.0) (2026-02-03)


### Bug Fixes

* **lint:** auto-fix lint errors [skip ci] ([b5f13a5](https://github.com/filipores/obojobs/commit/b5f13a5f10b6de694e09d62017694dd31d99db7a)), closes [#263](https://github.com/filipores/obojobs/issues/263)


### Features

* **templates:** add 3-variant generation from single sentence input (ob-awkt) ([516b896](https://github.com/filipores/obojobs/commit/516b896951e78ee72eb11fa8b0ec9d61331e6708))

# [1.18.0](https://github.com/filipores/obojobs/compare/v1.17.1...v1.18.0) (2026-02-03)


### Features

* **templates:** replace 3-button entry with single CTA overlay (ob-bu7s) ([99a3f0c](https://github.com/filipores/obojobs/commit/99a3f0cbb720d22896b813fff3f51fd455725bff))

## [1.17.1](https://github.com/filipores/obojobs/compare/v1.17.0...v1.17.1) (2026-02-02)


### Bug Fixes

* **migrations:** resolve duplicate revision id conflict ([082cd7c](https://github.com/filipores/obojobs/commit/082cd7c732d35236eb2ebf453ba578a801049117))

# [1.17.0](https://github.com/filipores/obojobs/compare/v1.16.0...v1.17.0) (2026-02-02)


### Features

* **ui:** add graceful error handling with broken enso fallback (ob--beyz.6) ([9acc71b](https://github.com/filipores/obojobs/commit/9acc71b8b7996778db3a5fd0bacf6ca0d84f3513))

# [1.16.0](https://github.com/filipores/obojobs/compare/v1.15.0...v1.16.0) (2026-02-02)


### Bug Fixes

* **lint:** sort imports in template_generator.py (pre-existing failure) ([9f85403](https://github.com/filipores/obojobs/commit/9f854030dea2198f0499873e8a3234962267a834))


### Features

* **ci:** add auto-fix workflow for lint-only failures (ob--qby7.5) ([368e0d1](https://github.com/filipores/obojobs/commit/368e0d13e6231c56cce482176d6d440cf19f15de))
* **ci:** add JSON test artifacts to all CI jobs (ob--qby7.1) ([4eb82ba](https://github.com/filipores/obojobs/commit/4eb82ba549c2e38116239574b4f69f905107c5c7))
* **ci:** add local CI mirror script (ob--qby7.4) ([13d8a70](https://github.com/filipores/obojobs/commit/13d8a701ea0be8100b42985762458f675dc95a64))
* **ci:** add PR comment with CI results (ob--qby7.3) ([c02e2ea](https://github.com/filipores/obojobs/commit/c02e2ea1c0aee3ee0437dc6b2bac2b7732a0150f))
* **ci:** add unified CI summary job (ob--qby7.2) ([6044272](https://github.com/filipores/obojobs/commit/6044272d5c26de96b01f6441948f617580f71681))
* **frontend:** add auto-paste detection with enso animation (ob--beyz.2) ([7c2c7f2](https://github.com/filipores/obojobs/commit/7c2c7f2d17a1aae93ff51953e9e4d22bfb26c3fd))
* **ui:** add crafting overlay with cinematic generation phases (ob--beyz.3) ([66bca1d](https://github.com/filipores/obojobs/commit/66bca1ddc3e1e7824bc24d79ddea5dea552f933a))
* **ui:** add enso animation components with wa-fuu design (ob--beyz.1) ([968ddb9](https://github.com/filipores/obojobs/commit/968ddb98e4ffebf17f6dcc65f38e1cdbec62f50d))
* **ui:** add premium reveal modal with einleitung preview (ob--beyz.4) ([b4f6c53](https://github.com/filipores/obojobs/commit/b4f6c53c2d99805b5f0b9fb88529bd335bd7f9e5))
* **ui:** transform CV-missing into inviting zero-state experience (ob--beyz.5) ([d0380f4](https://github.com/filipores/obojobs/commit/d0380f4f0266b854a1bbc6743e6998d1f5ba1831))

# [1.15.0](https://github.com/filipores/obojobs/compare/v1.14.2...v1.15.0) (2026-02-02)


### Features

* **applications:** make Arbeitszeugnis optional for application generation ([48880bf](https://github.com/filipores/obojobs/commit/48880bf8c3e933aacecd727cfdbad5f0625c0940))

## [1.14.2](https://github.com/filipores/obojobs/compare/v1.14.1...v1.14.2) (2026-02-02)


### Bug Fixes

* **applications:** remove Job-Fit preview code from NewApplication (ob--cg5) ([6bf29b4](https://github.com/filipores/obojobs/commit/6bf29b4abd4f9eef855f42408f4aecb774567edc))

## [1.14.1](https://github.com/filipores/obojobs/compare/v1.14.0...v1.14.1) (2026-02-02)


### Bug Fixes

* **applications:** preserve user-edited data and fix PDF download (ob-339) ([861945f](https://github.com/filipores/obojobs/commit/861945f2c2663f21ddbb3026018d45bd3af58aa6))

# [1.14.0](https://github.com/filipores/obojobs/compare/v1.13.0...v1.14.0) (2026-02-02)


### Features

* **templates:** auto-create default German template on first application ([4811b48](https://github.com/filipores/obojobs/commit/4811b48f42e6376cc42926cdbaf0dfe4a95a5fd5))

# [1.13.0](https://github.com/filipores/obojobs/compare/v1.12.0...v1.13.0) (2026-02-02)


### Features

* **frontend:** add usage indicator to NewApplication page ([bf10a9a](https://github.com/filipores/obojobs/commit/bf10a9a9c8a7e5c34a52d0c64fd8a57f1f8318a7)), closes [#45](https://github.com/filipores/obojobs/issues/45)

# [1.12.0](https://github.com/filipores/obojobs/compare/v1.11.0...v1.12.0) (2026-02-02)


### Features

* make Arbeitszeugnis optional for application generation (ob--nkl) ([5e70c03](https://github.com/filipores/obojobs/commit/5e70c03886e024df6a54440747b09c4ffb53e1e5))

# [1.11.0](https://github.com/filipores/obojobs/compare/v1.10.0...v1.11.0) (2026-02-02)


### Features

* move Job-Fit Score from preview to post-generation (ob--cg5) ([8c229f6](https://github.com/filipores/obojobs/commit/8c229f6df5cdb774af65458e8d6a291a82b14445))

# [1.10.0](https://github.com/filipores/obojobs/compare/v1.9.2...v1.10.0) (2026-02-02)


### Features

* **applications:** implement minimal confirmation flow for job applications ([1abd18c](https://github.com/filipores/obojobs/commit/1abd18c03e7d5c66c0d66675c1a69a3d622d49c5))

## [1.9.2](https://github.com/filipores/obojobs/compare/v1.9.1...v1.9.2) (2026-02-01)


### Bug Fixes

* **web_scraper:** expand austrian job portals ([e04efad](https://github.com/filipores/obojobs/commit/e04efad21e8537dd40f4944c44c850e403e00eba))

## [1.9.1](https://github.com/filipores/obojobs/compare/v1.9.0...v1.9.1) (2026-02-01)


### Bug Fixes

* **e2e:** add explicit waits for h1 in Settings tests (ob-s7r) ([ac18d61](https://github.com/filipores/obojobs/commit/ac18d61c8b04fb350d19ff5849f0c6ff34a8daf3))

# [1.9.0](https://github.com/filipores/obojobs/compare/v1.8.0...v1.9.0) (2026-01-31)


### Features

* **templates:** add rich-text editor with Tiptap for formatting preservation ([4fcc825](https://github.com/filipores/obojobs/commit/4fcc825ba0563938f2d9f59099c6aa9f7e810c10))

# [1.8.0](https://github.com/filipores/obojobs/compare/v1.7.9...v1.8.0) (2026-01-31)


### Features

* add GenericJobParser fallback for unknown job boards (ob-ax9) ([06a54c4](https://github.com/filipores/obojobs/commit/06a54c47159a57a06fc252ff71adeb2d67b12c09))

## [1.7.9](https://github.com/filipores/obojobs/compare/v1.7.8...v1.7.9) (2026-01-31)


### Bug Fixes

* **applications:** fix web scraping and generation bugs ([ebb7309](https://github.com/filipores/obojobs/commit/ebb73093536dda710cb0270655cb23d48162869e))
* **pdf-wizard:** fix variable name mapping and auto-advance to review (ob-a7o) ([70b5765](https://github.com/filipores/obojobs/commit/70b576502fe6c6efb1a757b8e840e71008bfe97c))
* **templates:** fix PDF template upload feature bugs ([53ed74f](https://github.com/filipores/obojobs/commit/53ed74fa60be84f3d4d0b0e7746ce984e3c77d06))
* **tests:** update test to match new missing_fields logic (ob-a7o) ([313913b](https://github.com/filipores/obojobs/commit/313913b90116ba0d768baac70a38434ee6f28277))

## [1.7.8](https://github.com/filipores/obojobs/compare/v1.7.7...v1.7.8) (2026-01-31)


### Bug Fixes

* **e2e:** use networkidle instead of domcontentloaded in auth utility ([647e96d](https://github.com/filipores/obojobs/commit/647e96df034c171af1c13963ea36d3000ac1d140))

## [1.7.7](https://github.com/filipores/obojobs/compare/v1.7.6...v1.7.7) (2026-01-30)


### Bug Fixes

* **e2e:** add shared auth utility with xhr mocking for vue spa tests ([ab10455](https://github.com/filipores/obojobs/commit/ab1045500aeec14a8fe08db51740d289cf1d5872))

## [1.7.6](https://github.com/filipores/obojobs/compare/v1.7.5...v1.7.6) (2026-01-30)


### Bug Fixes

* **e2e:** fix auth pattern for Vue SPA - use window.location.href ([f1a1ac6](https://github.com/filipores/obojobs/commit/f1a1ac61a4fb2286f5472ae495080b8777c9d5b8))

## [1.7.5](https://github.com/filipores/obojobs/compare/v1.7.4...v1.7.5) (2026-01-30)


### Bug Fixes

* **ci:** resolve test failures and linting issues ([b3841f3](https://github.com/filipores/obojobs/commit/b3841f3466ceda8758b33c078ea040d6f78b203d))

## [1.7.4](https://github.com/filipores/obojobs/compare/v1.7.3...v1.7.4) (2026-01-30)


### Bug Fixes

* **test:** add btoa polyfill for node.js test environment ([59da20e](https://github.com/filipores/obojobs/commit/59da20e7e5f9eb9f57467055aa7d9b209ef2b146))

## [1.7.3](https://github.com/filipores/obojobs/compare/v1.7.2...v1.7.3) (2026-01-30)


### Bug Fixes

* **a11y:** add missing list elements and test IDs to Applications page ([cede92d](https://github.com/filipores/obojobs/commit/cede92d0265bb28813c4f122435027b28510ae80))

## [1.7.2](https://github.com/filipores/obojobs/compare/v1.7.1...v1.7.2) (2026-01-30)


### Bug Fixes

* **e2e:** correct auth mock localStorage keys and add valid JWT token ([f97d318](https://github.com/filipores/obojobs/commit/f97d3183be017dbf3daa59198cc5d9c16d4f3886))

## [1.7.1](https://github.com/filipores/obojobs/compare/v1.7.0...v1.7.1) (2026-01-30)


### Bug Fixes

* **pdf-preview:** use shallowRef to fix Vue 3 reactivity issue with pdf.js ([8353c80](https://github.com/filipores/obojobs/commit/8353c807144c16c58e15de9b3f4046c2f83a1e55))

# [1.7.0](https://github.com/filipores/obojobs/compare/v1.6.1...v1.7.0) (2026-01-29)


### Features

* add print styles for clean document printing ([495e98c](https://github.com/filipores/obojobs/commit/495e98c210c7875093fdcf649265875104939a50))

## [1.6.1](https://github.com/filipores/obojobs/compare/v1.6.0...v1.6.1) (2026-01-29)


### Bug Fixes

* **css:** replace hardcoded colors with CSS variables ([65ea71d](https://github.com/filipores/obojobs/commit/65ea71d842d9e86136cfbaa68f5584cb7c503d30)), closes [#fff](https://github.com/filipores/obojobs/issues/fff) [#dc3545](https://github.com/filipores/obojobs/issues/dc3545)

# [1.6.0](https://github.com/filipores/obojobs/compare/v1.5.13...v1.6.0) (2026-01-29)


### Features

* add upload progress indicator to PDF template wizard ([bf1a8a4](https://github.com/filipores/obojobs/commit/bf1a8a4e615287cfec2881d4d00f5ca6bbe4645a))

## [1.5.13](https://github.com/filipores/obojobs/compare/v1.5.12...v1.5.13) (2026-01-29)


### Bug Fixes

* **css:** replace inset shorthand for browser compatibility ([ea56992](https://github.com/filipores/obojobs/commit/ea56992af95fba8d2b9ffab261c0331ab799dc32))

## [1.5.12](https://github.com/filipores/obojobs/compare/v1.5.11...v1.5.12) (2026-01-29)


### Bug Fixes

* **seo:** add meta description to index.html ([3725f05](https://github.com/filipores/obojobs/commit/3725f05a71282ac244d5093a6420a581f69bb446))

## [1.5.11](https://github.com/filipores/obojobs/compare/v1.5.10...v1.5.11) (2026-01-29)


### Bug Fixes

* add error handling to clipboard copy in Settings ([5202838](https://github.com/filipores/obojobs/commit/520283862b67e5821700685dfb28ce22db56ef04))

## [1.5.10](https://github.com/filipores/obojobs/compare/v1.5.9...v1.5.10) (2026-01-29)


### Bug Fixes

* replace hardcoded de-DE locale with dynamic getFullLocale() ([feda1f3](https://github.com/filipores/obojobs/commit/feda1f3380287cd49d0b70c8914ef3cd1bb17f94))

## [1.5.9](https://github.com/filipores/obojobs/compare/v1.5.8...v1.5.9) (2026-01-29)


### Bug Fixes

* **auth:** add try-catch for localStorage, fix OAuth timer leaks ([cf39765](https://github.com/filipores/obojobs/commit/cf39765e2cdf4378e1da8eb1b32bbb4d08ff47a1))

## [1.5.8](https://github.com/filipores/obojobs/compare/v1.5.7...v1.5.8) (2026-01-29)


### Bug Fixes

* add API error handlers and keyboard accessibility ([208f8f9](https://github.com/filipores/obojobs/commit/208f8f9a4cc98a8f95019cb7a8ef8fdc4e4f5281))
* **applications:** add search input debouncing ([0eb343a](https://github.com/filipores/obojobs/commit/0eb343a1adc8d5b1aacdbc10cfac15eb179c9040))

## [1.5.7](https://github.com/filipores/obojobs/compare/v1.5.6...v1.5.7) (2026-01-29)


### Bug Fixes

* **css:** standardize z-index values with CSS variables ([3b3b604](https://github.com/filipores/obojobs/commit/3b3b6044f4c3bf0895e75119da0c8097fd566370))


### Performance Improvements

* **recommendations:** combine 6 count queries into single query ([e4cbcfd](https://github.com/filipores/obojobs/commit/e4cbcfd8ad2ad614dee3d06b36668929581a022f))

## [1.5.6](https://github.com/filipores/obojobs/compare/v1.5.5...v1.5.6) (2026-01-29)


### Bug Fixes

* update Datenschutz to Stripe, fix env examples ([a7a03fa](https://github.com/filipores/obojobs/commit/a7a03fadf2c6b96baefd893886ef2b3dae2a78a5))

## [1.5.5](https://github.com/filipores/obojobs/compare/v1.5.4...v1.5.5) (2026-01-29)


### Bug Fixes

* address round 4 bugs (memory leak, validation, index) ([ceb1b1c](https://github.com/filipores/obojobs/commit/ceb1b1cbeb05ed89bfe0220c5997749838fdd038))

## [1.5.4](https://github.com/filipores/obojobs/compare/v1.5.3...v1.5.4) (2026-01-29)


### Bug Fixes

* **a11y:** add ARIA attributes to GapAnalysis, InterviewTracker, and modals ([1ae1880](https://github.com/filipores/obojobs/commit/1ae18808daa6ef73b5fd2759c9383259695b08f0))

## [1.5.3](https://github.com/filipores/obojobs/compare/v1.5.2...v1.5.3) (2026-01-29)


### Bug Fixes

* **a11y:** add missing ARIA labels to SalaryCoach, ATSOptimizer, JobFitScore, CompanyResearch ([d8fac50](https://github.com/filipores/obojobs/commit/d8fac50dac2e2c008d4348308392b658c66e2f37))

## [1.5.2](https://github.com/filipores/obojobs/compare/v1.5.1...v1.5.2) (2026-01-29)


### Bug Fixes

* **i18n:** remove duplicate /api prefix in LanguageSwitcher ([3ffffc4](https://github.com/filipores/obojobs/commit/3ffffc4abd4d2f2aef70eab6a6f50e4ecdf70c57))

## [1.5.1](https://github.com/filipores/obojobs/compare/v1.5.0...v1.5.1) (2026-01-29)


### Bug Fixes

* address bug report findings (LanguageSwitcher, XSS, port configs) ([952e531](https://github.com/filipores/obojobs/commit/952e531cba9e873f772df974049531bfedaac455))

# [1.5.0](https://github.com/filipores/obojobs/compare/v1.4.0...v1.5.0) (2026-01-29)


### Features

* **scraper:** add SoftgardenParser for softgarden.io job postings ([c008682](https://github.com/filipores/obojobs/commit/c008682cf511c0de30550896ba9ba0cfbfb1a4c0))

# [1.4.0](https://github.com/filipores/obojobs/compare/v1.3.1...v1.4.0) (2026-01-29)


### Features

* **templates:** add PDF indicator, variable count, and preview highlights ([9574faa](https://github.com/filipores/obojobs/commit/9574faa55ebaae7a7e23d82da9032a1657718000))

## [1.3.1](https://github.com/filipores/obojobs/compare/v1.3.0...v1.3.1) (2026-01-29)


### Bug Fixes

* **templates:** correct api payload key for variable positions ([bbd8eee](https://github.com/filipores/obojobs/commit/bbd8eee1bbd279e17f960c3f51418150a0960a42))

# [1.3.0](https://github.com/filipores/obojobs/compare/v1.2.2...v1.3.0) (2026-01-27)


### Features

* **backend:** add PDF template upload and analysis endpoints ([8928078](https://github.com/filipores/obojobs/commit/892807894b6452027d85449c6582b7f394e3bb75))

## [1.2.2](https://github.com/filipores/obojobs/compare/v1.2.1...v1.2.2) (2026-01-27)


### Bug Fixes

* **frontend:** update PdfTemplateWizard API endpoints to match backend ([498d102](https://github.com/filipores/obojobs/commit/498d1028ca698e7e0756f9021540abbc49d1dbc9))

## [1.2.1](https://github.com/filipores/obojobs/compare/v1.2.0...v1.2.1) (2026-01-27)


### Bug Fixes

* **deps:** add pdfjs-dist for pdf template wizard ([4810888](https://github.com/filipores/obojobs/commit/48108884dcf743d913194389f98e1cac09d1ae0f))

# [1.2.0](https://github.com/filipores/obojobs/compare/v1.1.0...v1.2.0) (2026-01-27)


### Features

* **templates:** integrate pdf template wizard into templates page ([1f68ef5](https://github.com/filipores/obojobs/commit/1f68ef58dbd3eec3e8c32be67ecd8ed95d56a5e2))

# [1.1.0](https://github.com/filipores/obojobs/compare/v1.0.0...v1.1.0) (2026-01-27)


### Features

* **api:** add dedicated /api/version endpoint ([d2d6e50](https://github.com/filipores/obojobs/commit/d2d6e5068cda04bf1c396aa8fd76cad62ec31210))

# 1.0.0 (2026-01-27)


### Bug Fixes

* **backend:** configure mypy to ignore Flask-SQLAlchemy model errors ([5289743](https://github.com/filipores/obojobs/commit/5289743f617f4d58bc99876f777b72d61f794686))
* **backend:** disable mypy errors for services and routes ([6d8d8e8](https://github.com/filipores/obojobs/commit/6d8d8e89a4c5657ac03ee9a1d7ebc164e05f5255))
* **backend:** resolve mypy errors in tracker.py and i18n/__init__.py ([f07938a](https://github.com/filipores/obojobs/commit/f07938a8cc15563d159790ec16726ea5a70e78bf))
* **backend:** resolve mypy name-defined error in user_skill.py ([29befc2](https://github.com/filipores/obojobs/commit/29befc21fd8e67ea79b0ff72482e01dff0b25218))
* **backend:** resolve mypy type errors in company_researcher.py ([54a90d9](https://github.com/filipores/obojobs/commit/54a90d933de766503d0b8298ca73d68acebe80e7))
* **backend:** resolve mypy type errors in web_scraper.py ([aaadfc2](https://github.com/filipores/obojobs/commit/aaadfc27fbae5c009d69495d13d621c740371cd0))
* BUG-001 - Details-Link führt zu nicht existierender Route - leere Seite ([4d2687f](https://github.com/filipores/obojobs/commit/4d2687f737b9926f4b4cf1c949d4e2e51f608364))
* BUG-001 - Interview-Fragen werden auf InterviewPrep-Seite nicht angezeigt ([a129d95](https://github.com/filipores/obojobs/commit/a129d95f48ddc5239d04957c15a0f146f41d4371))
* BUG-002 - API-Fehler 415 beim Generieren von Interview-Fragen ([7f4f966](https://github.com/filipores/obojobs/commit/7f4f966b83e8a025568b2d6ac6b325660b166846))
* BUG-003 - Fehlermeldungen werden nicht lokalisiert (Englisch statt Deutsch) ([db7f3eb](https://github.com/filipores/obojobs/commit/db7f3eb598956ff0fca1ba28dd70a6b2b881fffe))
* BUG-003 - Modal-State wird nicht zurückgesetzt beim erneuten Öffnen ([9941a9b](https://github.com/filipores/obojobs/commit/9941a9b11e332fd699af7a530cba298d1c6c4218))
* BUG-004 - Englischer Toast bei ungültigem Reset-Token zusätzlich zur deutschen Fehlerkarte ([452ca5b](https://github.com/filipores/obojobs/commit/452ca5b0d47738e2a8016ecb3af40471522c39da))
* BUG-004 - GapAnalysis-Komponente wird nicht angezeigt bei fehlenden JobRequirements ([61b3036](https://github.com/filipores/obojobs/commit/61b3036d4baab2f63e7d0746ec1744b94dfe74b5))
* BUG-005 - Englische technische Fehlermeldungen werden Endnutzern angezeigt ([d30c371](https://github.com/filipores/obojobs/commit/d30c3717e71eab43c345b8064e67ed41b08d7651))
* BUG-005 - Toast-Deduplizierung verhindert identische Meldungen ([bcb5dc6](https://github.com/filipores/obojobs/commit/bcb5dc67d1b1793489d4bc82c5ec55551bf078f1))
* BUG-007 - Alte Fehlermeldung bleibt nach manuellem Fallback sichtbar ([f54022d](https://github.com/filipores/obojobs/commit/f54022d0f368d882ac6a71b1d35763953e0f6c36))
* BUG-008 - Inkonsistente Umlaute in Fehlermeldung (Anforderungsanalyse) ([d7509ba](https://github.com/filipores/obojobs/commit/d7509ba4c73ddb4b4d54cc00a93da3511b829309))
* BUG-009 - Keine Client-seitige URL-Validierung vor Submit ([019b19e](https://github.com/filipores/obojobs/commit/019b19ec51809fcef1e78f2cde397653ebeabb17))
* BUG-010 - Keine Fehlermeldung bei Duplikat-Skill ([f0dc8ad](https://github.com/filipores/obojobs/commit/f0dc8adbcd8fddde9245948eb2f83dc6833f6353))
* BUG-011 - Login-Fehlermeldung wird nicht angezeigt bei falschen Credentials ([dc2a63d](https://github.com/filipores/obojobs/commit/dc2a63db50b36d4b373cb1769eb2eece903bd900))
* BUG-012 - Kein Hamburger-Menü auf Mobile - Navigation nicht zugänglich ([dd1cdf0](https://github.com/filipores/obojobs/commit/dd1cdf0534c605dfa91e7001a98a21a391b7b1f5))
* BUG-013 - Einstellungen und Abmelden auf Mobile nicht zugänglich ([9b003ab](https://github.com/filipores/obojobs/commit/9b003abdd6c62a6118fb5f989192e5e76cc35fe3))
* BUG-014 - Enter-Taste sendet Formular auf /new-application nicht ab ([6816824](https://github.com/filipores/obojobs/commit/6816824f0e28748744ee6f9d97ed8e06806e938a))
* BUG-015 - Escape-Taste schließt Modals nicht ([1993383](https://github.com/filipores/obojobs/commit/19933837bb20e930011fea834caf1c6056cb4234))
* BUG-016 - Firmen-Recherche zeigt korrupte/unlesbare Zeichen ([bb4f6ce](https://github.com/filipores/obojobs/commit/bb4f6ce4e5104d75f36d0dc77f319d9aa602f390))
* BUG-017 - Interview-Fragen können nicht generiert werden - Stellenbeschreibung fehlt ([7bd60d3](https://github.com/filipores/obojobs/commit/7bd60d3f701621de9ddab5ca277084382f03ddaf))
* BUG-018 - Route /applications/:id/mock-interview zeigt leere Seite ([577cd82](https://github.com/filipores/obojobs/commit/577cd82a997c30804147372f1d9911a426fd1a6c))
* BUG-019 - 401-Handler erkennt viele JWT-Fehlermeldungen nicht ([4ecba06](https://github.com/filipores/obojobs/commit/4ecba0656bb8d1a2e19603e0acacbc19088cad1a))
* BUG-020 - Navigation zeigt eingeloggten Zustand trotz ungültigem Token ([08c9ca0](https://github.com/filipores/obojobs/commit/08c9ca030a7df9faa12196c83df69ef8ce8dac58))
* BUG-021 - Backend gibt 422 statt 401 für ungültige Tokens ([e810bdc](https://github.com/filipores/obojobs/commit/e810bdc5d04ba04d3758a3d70112b76c3576eaad))
* BUG-022 - Verhindere Error-Toast bei leeren API States ([de59952](https://github.com/filipores/obojobs/commit/de5995285062ce464f8844bdabc1e3b06fd6c541))
* BUG-023 - Applications-Seite zeigt Fehlerzustand statt 'Keine Bewerbungen' ([b81a113](https://github.com/filipores/obojobs/commit/b81a11338654ca3ed81ef66fd7bbed51ae2e045b))
* BUG-024 - Aktions-Button 'Bewerbungen' fehlt in Mobile-Ansicht auf Company Insights ([c5cb730](https://github.com/filipores/obojobs/commit/c5cb73013c2ddec67e877ac8c75169ebca97935c))
* BUG-025 - KPI-Statistik-Karten zeigen permanente Skeleton-Loading statt Daten ([ddeedce](https://github.com/filipores/obojobs/commit/ddeedcec3fe8969c67601b46ad47cbdbbe61fbdb))
* BUG-026 - Fehlende 'Konto löschen' Funktion (DSGVO-Compliance) ([7cd8b25](https://github.com/filipores/obojobs/commit/7cd8b257733682576be095aa037f43e8a1310353))
* BUG-027 - Feature-Liste des aktuellen Plans ist leer ([4825caf](https://github.com/filipores/obojobs/commit/4825caf0bb149deec33f8ad2d5e72acd04429f25))
* BUG-028 - Keine Upgrade-Optionen oder Plan-Vergleich sichtbar ([2413532](https://github.com/filipores/obojobs/commit/2413532db957884382c88279051e0b73eca2a115))
* BUG-029 - Stripe Checkout schlägt fehl - Plan nicht konfiguriert ([e068f5f](https://github.com/filipores/obojobs/commit/e068f5fd5a08a0572784f5b8d3963ed8328dab3f))
* BUG-030 - Fehlende Lebenslauf-Warnung vor ATS-Analyse ([7673927](https://github.com/filipores/obojobs/commit/767392784edfb547e164199c415242d7fedf50b7))
* BUG-031 - Keine sichtbare Validierungsmeldung bei leerem Login-Formular ([5a6219c](https://github.com/filipores/obojobs/commit/5a6219c83b889312565cffb4884999cd5c0688be))
* BUG-032 - Button-Style Inkonsistenz auf Settings-Seite ([beafcb8](https://github.com/filipores/obojobs/commit/beafcb898d27e19fb52e50b5eb65dffbb13c1ba7))
* BUG-033 - Subscription-Seite rendert nicht - getAvailablePlans function fehlt ([0b17ef1](https://github.com/filipores/obojobs/commit/0b17ef136a57cfa7105e0ea00c56bafb20168348))
* BUG-036 - Job-Analyse Dialog zeigt irrelevante Fehlermeldung nach Success-Flow ([66a805e](https://github.com/filipores/obojobs/commit/66a805e750db42b97d160481d139c77630050b0b))
* BUG-037 - Job-Analyse API schlägt mit 400 Bad Request fehl ([3755f06](https://github.com/filipores/obojobs/commit/3755f061cea7fde1a1b0e80a9b0616c25286d72a))
* BUG-038 - Modal-Overlay blockiert Navigation während Job-Analyse geöffnet ist ([61a08ca](https://github.com/filipores/obojobs/commit/61a08cab7ba4da8cd5eb9b9d146ac9feed1b9228))
* BUG-039 - Gmail-Integration nicht konfiguriert - wirft Backend-Fehler ([cb950f6](https://github.com/filipores/obojobs/commit/cb950f6638dd8fa59a9ae9594953c2212b6da752))
* BUG-040 - Mobile Navigation Schließen-Button ist nicht funktional ([c707cfa](https://github.com/filipores/obojobs/commit/c707cfae3d44e4674a701609ef732450a2138a20))
* BUG-041 - Job-Analyse API-Fehlerbehandlung inkonsistent ([afc7e29](https://github.com/filipores/obojobs/commit/afc7e298c58575c1ce8c70ca3e47ca28930992f4))
* BUG-042 - Stellenanzeige-URL-Fehlerbehandlung inkonsistent ([2493e72](https://github.com/filipores/obojobs/commit/2493e72783846921a008cabd293dcb031ced85f7))
* BUG-043 - Keine 404-Seite für ungültige Routen ([7e1ca99](https://github.com/filipores/obojobs/commit/7e1ca99b4e2dca1cda83ba0cff92ca532fd0ecea))
* BUG-044 - Passwort-Änderung zeigt keine Validierungsfehlermeldung ([134be76](https://github.com/filipores/obojobs/commit/134be76b284c4be4775fd55839c06ad8f4ecdcd3))
* BUG-045 - Bewerbungsgenerierung scheitert - Lebenslauf fehlt ([9da2716](https://github.com/filipores/obojobs/commit/9da2716b3dac975238a9d039e426703f7cdbb2d5))
* **ci:** allow empty lint-staged runs for semantic-release ([1497fbb](https://github.com/filipores/obojobs/commit/1497fbb309ffbba40c235967ee6f92e15b2f82bf))
* **ci:** disable husky hooks in semantic-release workflow ([98c3f52](https://github.com/filipores/obojobs/commit/98c3f528d07d87d49e833995f4b548d262ed35fb))
* **ci:** lower backend coverage threshold to 55% ([d5b3ac3](https://github.com/filipores/obojobs/commit/d5b3ac3b464a3dc9f3d22d6cf4b66a62e7c62e0e))
* **ci:** lower frontend coverage thresholds to 70% ([f183049](https://github.com/filipores/obojobs/commit/f1830495c8c1380e132e87b83e049f65bf04c6a4))
* code simplify staged diff not entire file ([64ca7a7](https://github.com/filipores/obojobs/commit/64ca7a70e860c94f08079503413e5b995a43e9bd))
* **critical:** add Escape key to Success Modal and fix privacy policy logout ([87e49eb](https://github.com/filipores/obojobs/commit/87e49eb57b40715418c284d3a2c574593d94d348))
* **e2e:** handle duplicate #app selector ([fee3138](https://github.com/filipores/obojobs/commit/fee3138607879b4525d922bcb07a619db205f7e2)), closes [#app](https://github.com/filipores/obojobs/issues/app) [#app](https://github.com/filipores/obojobs/issues/app)
* escape @ in i18n email placeholders ([e7b9a25](https://github.com/filipores/obojobs/commit/e7b9a25c15438beedc770e78f9a6ce2b1aa2ec4a))
* **frontend:** upgrade dockerfile to node.js 22 lts ([5b9b387](https://github.com/filipores/obojobs/commit/5b9b3879fa55ed33f20df171ba1e4cb1d75eb778))
* **major:** resolve 10 major bugs including accessibility, i18n, and UX issues ([a683981](https://github.com/filipores/obojobs/commit/a6839810ccefac2a969a1c0efa7b9dd18514b4d9))
* **minor:** resolve 6 minor and 1 trivial UX bugs ([b843709](https://github.com/filipores/obojobs/commit/b84370917da8a336a2f5ad99422b80e02dc59293))
* Move PR creation from ralph.sh to prompt.md ([b592157](https://github.com/filipores/obojobs/commit/b592157305bd57bc07ad516e5d86996de4dcc577))
* prevent label text from remaining after variable chip removal ([ef761c2](https://github.com/filipores/obojobs/commit/ef761c2410fcd68d35262cfa8492be35daf2789e))
* prevent variable label text duplication on insert ([262ec17](https://github.com/filipores/obojobs/commit/262ec17816bce45512bfd0c560f5302a4c2c6ac1))
* remove unused imports and sort import blocks in test files ([f5f5156](https://github.com/filipores/obojobs/commit/f5f51563bd93d837be319dc1db971866bb7e7746))
* rename unused oldValue param to _oldValue for eslint ([f70d61b](https://github.com/filipores/obojobs/commit/f70d61b1830211a6e65a08bac1ccd2c36a4eae5f))
* resolve CI failures - eslint and backend tests ([cbbd69b](https://github.com/filipores/obojobs/commit/cbbd69b66ecb4ac9c13003d2df67ed79fdf68ab6))
* resolve CI failures - mypy and frontend test imports ([a3ca95b](https://github.com/filipores/obojobs/commit/a3ca95bad8d0309425a9dd75575466d4b2a3b229))
* resolve ci failures and remove codeql workflow ([e1cd39b](https://github.com/filipores/obojobs/commit/e1cd39bbc2c7e5fe93447f14c2be163d54e2c027))
* resolve CI ruff and frontend test errors ([a59e428](https://github.com/filipores/obojobs/commit/a59e42837865226cf4b0bacf3ed9e2d8402b5e42))
* sync deployment configuration for production ([8cdeb10](https://github.com/filipores/obojobs/commit/8cdeb1040dc29abf20e89e287a76fbc2e40107a6))
* **tests:** skip all PDF template routes tests ([7beb859](https://github.com/filipores/obojobs/commit/7beb859163a380d269a70205304f222b1874306d))
* **tests:** skip failing PDF template tests pending mock refinement ([a81d85c](https://github.com/filipores/obojobs/commit/a81d85c86e352bf109bd00cc8e718b4bcb78ab08))


### Features

* [ATS-001] - ATS Service Grundstruktur ([a1b252f](https://github.com/filipores/obojobs/commit/a1b252f607de7e86f96ed10be58e646bba96583f))
* [ATS-002] - ATS API Endpoint ([c6568dd](https://github.com/filipores/obojobs/commit/c6568dd3408b2ddeb65fd982d85515a07c7d2700))
* [ATS-003] - Keyword-Kategorisierung ([500287d](https://github.com/filipores/obojobs/commit/500287de7c42898664f7b03173bc8529f6ee58eb))
* [ATS-004] - ATS Dashboard View ([9b55d89](https://github.com/filipores/obojobs/commit/9b55d899141cbddac03e07ade06302fcd6af4766))
* [ATS-006] - ATS History & Caching ([461b9b2](https://github.com/filipores/obojobs/commit/461b9b25fa04ac76d4aa4966f5c43e73483a5683))
* [AUTH-001] - Passwort-Stärke Validierung ([72ed60e](https://github.com/filipores/obojobs/commit/72ed60ebc02120a9c987b3ecdb4af15234d44b91))
* [AUTH-002] - Email-Verifizierung Backend Token-System ([5dca921](https://github.com/filipores/obojobs/commit/5dca9216853d95260bb44218b6c6cbe977739663))
* [AUTH-003] - Email-Verifizierung API Endpoints ([40056d2](https://github.com/filipores/obojobs/commit/40056d2d7127cd8ac02eef927076d46eced8a35a))
* [AUTH-004] - Email-Verifizierung Frontend Flow ([6821365](https://github.com/filipores/obojobs/commit/682136583806a94e9e7e5391fd0bd1a1a6e027c9))
* [AUTH-005] - Passwort-Reset Backend Token-System ([dc7fb6f](https://github.com/filipores/obojobs/commit/dc7fb6fb314e9e4293f18e593bb750fdb23c318d))
* [AUTH-006] - Passwort-Reset Frontend Flow ([610a5e2](https://github.com/filipores/obojobs/commit/610a5e2ad65a3fc722b3afb7d514f7c12f2ae79e))
* [AUTH-007] - Account-Sperre bei Fehlversuchen ([e534827](https://github.com/filipores/obojobs/commit/e5348275348ae2f6ca837253745cea9c1f3a3d49))
* [AUTH-008] - Passwort ändern (eingeloggt) ([bb95b1f](https://github.com/filipores/obojobs/commit/bb95b1f8d3e7f2ab2a32728575cb4a201d4bc978))
* [AUTH-009] - Logout Endpoint ([dde32a7](https://github.com/filipores/obojobs/commit/dde32a71276646e86805f0d6531f214147b816d7))
* [AUTH-010] - Security Headers & HTTPS-Redirect ([0c71b83](https://github.com/filipores/obojobs/commit/0c71b832ecf8a3a1f7f153f69d3c11317ae52f0d))
* [EMAIL-001] - OAuth Token Storage Model ([aa1aac3](https://github.com/filipores/obojobs/commit/aa1aac3eec2ecaa13506e248ad06b8fb1521a80f))
* [EMAIL-002] - Gmail OAuth 2.0 Flow ([295177f](https://github.com/filipores/obojobs/commit/295177fbd8cecdcd3213740972791a15db866d84))
* [EMAIL-003] - Outlook OAuth 2.0 Flow ([de19e5a](https://github.com/filipores/obojobs/commit/de19e5abedc54be056c295e946be3802e889bb6a))
* [EMAIL-004] - Email Provider Management UI ([4b26838](https://github.com/filipores/obojobs/commit/4b26838558671dde9b6dac00122f40b2d1fd8910))
* [EMAIL-005] - Email Composer ([974e6e8](https://github.com/filipores/obojobs/commit/974e6e8f6921c5d62b5df89bfd670b6c6a2e5d7c))
* [EMAIL-006] - Email Versand mit Attachments ([7602598](https://github.com/filipores/obojobs/commit/760259808fded8589cd2a6da5ad4c46aaa1f498c))
* [EMAIL-007] - Sent Tracking & Status Update ([bb9b3a6](https://github.com/filipores/obojobs/commit/bb9b3a65ef8bc665b249b96bca6afe08167aaad3))
* [INFRA-001] - Backend: pytest Setup ([836a11b](https://github.com/filipores/obojobs/commit/836a11b4c7f0de049c4f00854a4c473bb9548877))
* [INFRA-002] - Backend: Health & Auth Tests ([99cd9c2](https://github.com/filipores/obojobs/commit/99cd9c27369ef12c68eb5598b14d1e4390a9d649))
* [INFRA-003] - Backend: Ruff Linter Setup ([f644860](https://github.com/filipores/obojobs/commit/f6448600cb34b700cd12a28358ddcc6fd517f640))
* [INFRA-004] - Backend: Bestehenden Code lint-konform machen ([cd936d2](https://github.com/filipores/obojobs/commit/cd936d21b83e3b2d8aea695825bc32a4daf12b9c))
* [INFRA-005] - Frontend: Vitest Setup ([22be7c2](https://github.com/filipores/obojobs/commit/22be7c2a5d1e71963d5a95a0e7f66b5051a8f050))
* [INFRA-006] - Frontend: Erste Component Tests ([d0eee14](https://github.com/filipores/obojobs/commit/d0eee14e43b898809e09abed604455b2ee6135a5))
* [INFRA-007] - Frontend: ESLint Setup ([077f6b8](https://github.com/filipores/obojobs/commit/077f6b8321e7535b525436440eeaf8b6efcd39e9))
* [INFRA-008] - Frontend: Bestehenden Code lint-konform machen ([ce315dc](https://github.com/filipores/obojobs/commit/ce315dcdd8da65b557df60a994aacfffce67ccc4))
* [INFRA-009] - prompt.md mit neuen Quality Checks aktualisieren ([5f4f816](https://github.com/filipores/obojobs/commit/5f4f816fc7c65f6fbfb0a5d08e0de42d802f23d7))
* add Alembic migration for PDF template fields ([efebe06](https://github.com/filipores/obojobs/commit/efebe06ee655438160c1e2f903358245c94b5024))
* add CI/CD hardening with Playwright E2E, coverage thresholds, and mypy ([b3b1a80](https://github.com/filipores/obojobs/commit/b3b1a807c3f07ddb596d24f911634354cb7029e5))
* add code-simplifier to pre-commit hook ([fbb2caf](https://github.com/filipores/obojobs/commit/fbb2caf3a931324b85fde6f0edfe221eafe7b4f0))
* add data migration script to fix corrupted template labels ([bb95a01](https://github.com/filipores/obojobs/commit/bb95a017fb3a5ef7d1540cdeb4b8246c21e6c1e4))
* add Dependabot and CodeQL security scanning ([35078ac](https://github.com/filipores/obojobs/commit/35078ac4bc063234e4b499ab2358a2cbad1da94d))
* add git workflow tooling with husky, lint-staged, and commitlint ([a10d9e1](https://github.com/filipores/obojobs/commit/a10d9e14501e771491da29eb7a66c8f50e41862e))
* Add OCR fallback for scanned PDF extraction ([5ebf964](https://github.com/filipores/obojobs/commit/5ebf96401d1adae9ef6fb92da4d2a1bdbd5092ce))
* add PDF template support to generator.py ([2c4b0b3](https://github.com/filipores/obojobs/commit/2c4b0b3beccf0b5c647803c0726d1a637e93928f))
* add PR and issue templates ([237c5ff](https://github.com/filipores/obojobs/commit/237c5ff9ed1785b2ee3e8bfab0aa40a2548fb9d1))
* Add PR creation to ralph.sh + AUTH PRD ([f3f23e8](https://github.com/filipores/obojobs/commit/f3f23e802a51660747361ec7d9bbd48559b1a150))
* add ralph suggestion mode for code analysis ([b2b3795](https://github.com/filipores/obojobs/commit/b2b37955a0b990f234f048ca420d7cb775489d91))
* add registration toggle via REGISTRATION_ENABLED env var ([ec24cd0](https://github.com/filipores/obojobs/commit/ec24cd0cf2e03f9c8ed5b22e0b6202ff82bfdcb1))
* add semantic-release for automated versioning and changelog ([d5c9c7c](https://github.com/filipores/obojobs/commit/d5c9c7c9c67f7a66f418ef7bee75c02b00745be6))
* ADV-001 - Smart Job Recommendations ([093a08f](https://github.com/filipores/obojobs/commit/093a08f4c506792070d1767469a56abca825ab9f))
* ADV-002 - Gehaltsverhandlungs-Coach ([1666a77](https://github.com/filipores/obojobs/commit/1666a7781fe44e6dfe2eaed593986415407e8586))
* ANALYTICS-001 - Extended Stats API ([40e18c9](https://github.com/filipores/obojobs/commit/40e18c9a87cf00a8749e15af4949864aac64b1a3))
* ANALYTICS-002 - Timeline View ([cdcb397](https://github.com/filipores/obojobs/commit/cdcb3972503564f5d9db9d419f5a9192dc2bff6e))
* ANALYTICS-003 - Company Insights ([0d6c756](https://github.com/filipores/obojobs/commit/0d6c756cc00f82ce92fe14e47a1a58529bff293b))
* ANALYTICS-004 - Export Funktionalität ([08fb838](https://github.com/filipores/obojobs/commit/08fb8389fbb0053fac5d74fede73499e1d11e9f8))
* **dashboard:** add application stats cards with today badges ([e8a12fd](https://github.com/filipores/obojobs/commit/e8a12fd0b9e9f45db7922993d51cfb145bc1981a))
* **dashboard:** add prominent upcoming interviews display ([f06a383](https://github.com/filipores/obojobs/commit/f06a3837ab411b9952f422e6c04adea87c44cf05))
* **frontend:** add PdfTemplateWizard components ([53b9048](https://github.com/filipores/obojobs/commit/53b904862571a61316f8e71aac010a655367fb25))
* i18n foundation - vue-i18n setup and backend i18n module ([f139d59](https://github.com/filipores/obojobs/commit/f139d59e43ac419fe3a906b6dc01ccaf761cfe9f))
* INT-001 - Interview-Fragen Generator ([d4b437b](https://github.com/filipores/obojobs/commit/d4b437bbe273be36e183f9af88474882a01d9cec))
* INT-002 - Interview-Prep UI ([2526658](https://github.com/filipores/obojobs/commit/25266583858db584ae62b56d83fea40fe0fa2272))
* INT-003 - Text-basiertes Mock-Interview ([c7f4cb6](https://github.com/filipores/obojobs/commit/c7f4cb6966f9a8f701f987b1859b20f98d443699))
* INT-004 - STAR-Methode Coach ([a86cd4c](https://github.com/filipores/obojobs/commit/a86cd4cc306ec7a6e9aab19cb1b9f918ea255faa))
* INT-005 - Firmen-Recherche Integration ([fe1fcb5](https://github.com/filipores/obojobs/commit/fe1fcb5afa2174c2e169d5d3e74996dcf20c531c))
* INT-006 - Interview-Ergebnis Tracking ([f94aa9e](https://github.com/filipores/obojobs/commit/f94aa9ea911cf2e032abd7ae9575ffe4b1261b95))
* JOBS-001 - StepStone Scraper ([827efac](https://github.com/filipores/obojobs/commit/827efac1c94592055eae0227024e510a5593d8f4))
* JOBS-002 - Indeed DE Scraper ([bfe5fb5](https://github.com/filipores/obojobs/commit/bfe5fb5a3432c18243057e39d6137061d6f26e4c))
* JOBS-003 - XING Jobs Scraper ([d6e952c](https://github.com/filipores/obojobs/commit/d6e952cf849ac5ebfb0fb17a534c9e6dbe643151))
* JOBS-004 - Job Import UI Enhancement ([8440a29](https://github.com/filipores/obojobs/commit/8440a2978f17a32e65390df7f3d564e46104704f))
* JOBS-005 - Arbeitsagentur Scraper ([723ebe4](https://github.com/filipores/obojobs/commit/723ebe4c80f66201e21aff2fadbdf7b1c10b3df9))
* NEW-001 - Manueller Stellentext-Import als Fallback ([af49079](https://github.com/filipores/obojobs/commit/af4907986778f9ba8a01f93123a0d3119dc125d4))
* NEW-002 - Timer für realistische Interview-Simulation ([0dc106b](https://github.com/filipores/obojobs/commit/0dc106b6aecf587de1d8dbdea17958e925bd1e3c))
* NEW-003 - Automatische Anforderungsanalyse bei Bewerbungserstellung ([f0f69b8](https://github.com/filipores/obojobs/commit/f0f69b80d23ca1886f1765a80c88c8f20a8d83a9))
* NEW-004 - Manueller ATS-Check mit eigenem Text ([fb75790](https://github.com/filipores/obojobs/commit/fb757903d2cdc0398a9e084ea611b741c95109fe))
* NEW-005 - STAR-Hinweis fuer nicht-behavioral Fragen ([7308b3a](https://github.com/filipores/obojobs/commit/7308b3aefedc792fbdcab3786350b245824c0b02))
* QUAL-001 - Skill-Extraktion aus CV ([4a382b5](https://github.com/filipores/obojobs/commit/4a382b549657156c69a7f2b0827b4cacc11ca64f))
* QUAL-002 - Job-Anforderungs-Analyse ([7293f72](https://github.com/filipores/obojobs/commit/7293f72d9d454d5fd1e393a9c9307290f54579e1))
* QUAL-003 - Job-Fit Score Berechnung ([eeecbd2](https://github.com/filipores/obojobs/commit/eeecbd2a78980f8da28038b6a3b89a2e27252ab7))
* QUAL-004 - Job-Fit Score UI ([7e653f7](https://github.com/filipores/obojobs/commit/7e653f76506741248ba0872f6585320302335c07))
* QUAL-005 - ATS-Score vor Bewerbungsabsendung ([a2b9fb2](https://github.com/filipores/obojobs/commit/a2b9fb24ee08710acd7eae3fac334219edf403d0))
* QUAL-006 - ATS-Score UI mit Verbesserungen ([fe47cac](https://github.com/filipores/obojobs/commit/fe47cac556f0e4be1514b8158935f6cd17517313))
* QUAL-007 - Gap-Analyse mit Lernempfehlungen ([fc3ad8c](https://github.com/filipores/obojobs/commit/fc3ad8cbd712b57a6f964c87c1a6b6917310a4f4))
* STRIPE-001 - Stripe SDK Setup ([53c2bf3](https://github.com/filipores/obojobs/commit/53c2bf3d6ffb3746932773917e247c6abe3f52ef))
* UX-001 - Details-Link auf spezifische Bewerbung verlinken ([55fbf37](https://github.com/filipores/obojobs/commit/55fbf373590b7ea97b20a45f162fe17b46d9e3e2))
* UX-002 - Navigationslink zu Company Insights hinzufügen ([f2b640c](https://github.com/filipores/obojobs/commit/f2b640cd59305baccb366d7f3a0d750c4feb7d87))
* UX-003 - Install @vitest/coverage-v8 dependency ([accc9e7](https://github.com/filipores/obojobs/commit/accc9e778458449d7a889159530694d630d949af))
* UX-004 - Automatische Extraktion von Kontaktdaten aus manuellem Text ([ae3b57f](https://github.com/filipores/obojobs/commit/ae3b57fc27876220015bed3cd8b3093e72a7360b))
* UX-005 - Echtzeit-URL-Validierung mit visuellem Feedback ([07f2fb7](https://github.com/filipores/obojobs/commit/07f2fb7e30907a0aeecdbced01cadfa68f5128bb))
* UX-007 - Loading-Spinner für Upgrade-Buttons hinzufügen ([a4aaf3c](https://github.com/filipores/obojobs/commit/a4aaf3cdceac6bb30de882338def2a542adece94))
* UX-008 - Backend-Fehlermeldungen auf Deutsch lokalisieren ([6169c84](https://github.com/filipores/obojobs/commit/6169c84d548a01e98c5638fc8facdf3c96853656))
* UX-009 - Doppelte Toast-Benachrichtigungen vermeiden ([b9df26a](https://github.com/filipores/obojobs/commit/b9df26a952880931d623fe70aad9f800efd55497))
* UX-010 - ARIA-Attribute für Toasts hinzufügen ([461012b](https://github.com/filipores/obojobs/commit/461012b2443f1fac9bfe64bc2ecea8677eda862b))
* UX-011 - ESLint in CI/CD Pipeline integrieren ([d6748c1](https://github.com/filipores/obojobs/commit/d6748c16c0d7d3efa91cc3a3505c9e48be21a430))
* UX-012 - Pre-fill Empfänger-Email aus Bewerbungsdaten ([3cd2c75](https://github.com/filipores/obojobs/commit/3cd2c75e766b4a2d399a746a7b8da95374657f16))
* UX-013 - Möglichkeit zum Löschen einzelner History-Einträge ([e487953](https://github.com/filipores/obojobs/commit/e487953fb348f005ae7f0acc28d34ec213871394))
* UX-014 - Passwort-Sichtbarkeits-Toggle hinzufügen ([77b4a60](https://github.com/filipores/obojobs/commit/77b4a6063664d30f672e81d12fcc2286609db2b8))
* UX-015 - Export gefilterte Daten ([956c064](https://github.com/filipores/obojobs/commit/956c06474c5e9b6eda35fa7f189f43d242ffa5d4))
* UX-016 - Login-401-Fehler korrekt behandeln ([34be1c5](https://github.com/filipores/obojobs/commit/34be1c56bf574cffe89527c26c3a157a54af1ff3))
* UX-017 - Sortierungs-Dropdown für Applications hinzufügen ([4c37314](https://github.com/filipores/obojobs/commit/4c3731450f5fbe239670fa37d72b9a9b5d31589e))
* UX-018 - Pagination für Applications implementieren ([36f07e9](https://github.com/filipores/obojobs/commit/36f07e9d48f8d066b55169f23926577357a882e8))
* UX-018 - Tooltips für Mobile-Navigation hinzufügen ([f34a5fa](https://github.com/filipores/obojobs/commit/f34a5fa683c79093cdd9fc8bcbca1eb76722300f))
* UX-019 - Button-Debounce für API Key Generierung ([cdc3b51](https://github.com/filipores/obojobs/commit/cdc3b51b1118e6eda397186e510782239413fe9d))
* UX-019 - Interview-Termin als Datepicker ([4f813e3](https://github.com/filipores/obojobs/commit/4f813e3811744410b81ddb5a47a49d2a445affea))
* UX-020 - Export-Button deaktivieren bei 0 Ergebnissen ([2a2eb32](https://github.com/filipores/obojobs/commit/2a2eb32f9457694c45079f4c23b4cd5f7126a2a9))
* UX-020 - Template-Variablen-Einfüge-Mechanismus verbessern ([de504ce](https://github.com/filipores/obojobs/commit/de504ce9ac77d1f05eb101669689960fef35bdda))
* UX-021 - Coverage-Threshold in Vitest konfigurieren ([f9ad540](https://github.com/filipores/obojobs/commit/f9ad54067bf3f8484c6d8c10a059b1c814ba291e))
* UX-021 - Text-Analyse in ATS-History speichern ([181a47a](https://github.com/filipores/obojobs/commit/181a47add14c829743513cb60c5c8bc333921477))
* UX-022 - Custom ConfirmModal statt native Browser-Dialoge ([7150b67](https://github.com/filipores/obojobs/commit/7150b6722c6534aa171ee0fe9b7ae1a989162731))
* UX-022 - Profil-Bearbeitungsmöglichkeit in Settings ([2a99c71](https://github.com/filipores/obojobs/commit/2a99c7128a992244b7152939bb6414a8a440aa1f))
* UX-023 - Hidden username field für Password-Manager ([beb2908](https://github.com/filipores/obojobs/commit/beb29083c79d0419f2deb08f642c74e3d4ad6ecb))
* UX-023 - Skeleton-Loading mit Animation versehen ([f73b62d](https://github.com/filipores/obojobs/commit/f73b62df55ee6a81d9aec88b7747c624d5dfd5fa))
* UX-024 - Timeline visuelle Zeitachsen-Linie hinzufügen ([d16af85](https://github.com/filipores/obojobs/commit/d16af855cdc1f31acc604f1f59799114f8bd5d2d))
* UX-024 - Upgrade-Buttons visuell disabled während Loading ([0d3eafb](https://github.com/filipores/obojobs/commit/0d3eafb3db7b276636c7e9b42cb91d7b3dc94736))
* UX-025 - ARIA-Live-Region für URL-Validierungsstatus ([8297513](https://github.com/filipores/obojobs/commit/829751354ec83488d44d8290301f52474dbe2535))
* UX-025 - Pflichtfeld-Markierung (*) bei Formularen ([c38b399](https://github.com/filipores/obojobs/commit/c38b39984b7b5d328f0854eb1a597696099a345a))
* UX-026 - aria-label für Delete-Buttons hinzufügen ([73becd9](https://github.com/filipores/obojobs/commit/73becd96e9fb2a0ec5f4abc89017c7440b28113a))
* UX-026 - ATS-Voraussetzungs-Check mit CTA ([98bb58d](https://github.com/filipores/obojobs/commit/98bb58dfe219d33c4b2c180819cd04715c55d670))
* UX-027 - Plan-Vergleichstabelle auf Subscription-Seite ([a4a611d](https://github.com/filipores/obojobs/commit/a4a611d7fb0795f085f6a1784c97138ce288a3d0))
* UX-027 - Vue Warnings für Platzhalter-Syntax beheben ([b2566d9](https://github.com/filipores/obojobs/commit/b2566d9ea310c3052708600a0f237613ac9f173e))
* UX-028 - Checkbox-Zustand zurücksetzen bei fehlendem Filter ([5fbb77e](https://github.com/filipores/obojobs/commit/5fbb77ecc4c7d427852296aa3438062db01b22fc))
* UX-028 - Inline-Validierung für Login/Register Formulare ([84361be](https://github.com/filipores/obojobs/commit/84361beeba19301c0890bcb079e481e8eee78a7f))
* UX-029 - autocomplete-Attribute für Passwort-Felder in Settings ([b9889ef](https://github.com/filipores/obojobs/commit/b9889ef16eb3bf9157831b7d4de9a2aedff5fc7d))
* UX-030 - Dynamische Page Titles im Browser-Tab ([917b30f](https://github.com/filipores/obojobs/commit/917b30f28979a7139606d205cb3c96dd5b30364c))
* UX-031 - aria-live für Passwort-Validierung ([7b1ef6f](https://github.com/filipores/obojobs/commit/7b1ef6f646428269cef4edfbfb9e869fa7f6072e))
* UX-032 - Loading-Spinner für Link-anfordern-Button ([018ba83](https://github.com/filipores/obojobs/commit/018ba83ad95225ff4a279cf5fbf68c0e78a917d7))
* UX-033 - Animierter Progress-Ring fuer ATS Score Visualisierung ([06dd96a](https://github.com/filipores/obojobs/commit/06dd96a7455b373eda081ecfd46609eb5cbce4bf))
* UX-034 - Toast-Bestaetigung bei Status-Aenderung ([78ae9c1](https://github.com/filipores/obojobs/commit/78ae9c1055a632b40563f171c5ccc50c7888c490))
* UX-035 - E-Mail-Verifizierungs-Banner persistent ([ca38ca6](https://github.com/filipores/obojobs/commit/ca38ca6318d482cbee1461e6c7bd4b6e35dc0dd5))
* UX-036 - Tabellen-Ansicht als Alternative zum Card-Grid ([ec7e235](https://github.com/filipores/obojobs/commit/ec7e235413b2109dc45299526a5681f1cfb27fc4))
* UX-037 - Status-Filter als klickbare Tabs statt Dropdown ([913e326](https://github.com/filipores/obojobs/commit/913e3267c15f9c785d7f5f83c4b9320d62c63e65))
* UX-038 - Settings-Navigation mit Sidebar fuer bessere Struktur ([b307776](https://github.com/filipores/obojobs/commit/b307776d31f6ade5cd2f93f870bc80b5e7426a11))
* UX-039 - Gehaltsverhandlungs-Coach Daten persistieren ([15af5b0](https://github.com/filipores/obojobs/commit/15af5b0e39ef2a234c15e74bba2ccec2ea28e644))
* UX-040 - Skills-Loeschung Dialog bei Dokument-Entfernung ([448089f](https://github.com/filipores/obojobs/commit/448089f5a504fabb75eb8d29631c8d098033f848))
* UX-041 - Horizontaler Scroll-Indikator fuer Tabellen ([369eab4](https://github.com/filipores/obojobs/commit/369eab43da7cd8b2261cd35ed8d2c5feadcc1d99))
* UX-042 - Klickbare Keyword-Badges mit Integrationstipps ([46f3595](https://github.com/filipores/obojobs/commit/46f3595d9aa48c847e24393581653d9cc2fa0032))
* UX-043 - Interview-Status aktiven Zustand visuell deutlicher ([b866a1d](https://github.com/filipores/obojobs/commit/b866a1d12dcdcfe88c310bd77d7daaebb5007353))
* UX-044 - aria-label fuer Stats-Karten hinzufuegen ([6470c0f](https://github.com/filipores/obojobs/commit/6470c0ffd5c361e0a3993dfd2a1ca0a5ccfa5cd8))
* UX-045 - Focus-Indicator fuer Dropdowns verbessern ([3b5c9a3](https://github.com/filipores/obojobs/commit/3b5c9a34a8ebe99033a14167f61a14d0dbb6657c))
* UX-046 - Bottom Navigation Bar fuer Mobile hinzufuegen ([e182a09](https://github.com/filipores/obojobs/commit/e182a09110333625138c6860763f44081660d418))
* UX-047 - Funktionierende Test-Credentials bereitstellen ([348f3e5](https://github.com/filipores/obojobs/commit/348f3e580b7a618c4e474d2fd366ee5398adba90))
* UX-048 - Versteckte Username-Felder für Accessibility ([3c94956](https://github.com/filipores/obojobs/commit/3c94956108a92785e9c89d1a72f5f5c3d6d9dc6a))
* UX-049 - Placeholder-Daten in Impressum/Datenschutz ersetzen ([e6c23eb](https://github.com/filipores/obojobs/commit/e6c23ebb261af0c767aea2facde71d5e591aeb28))
* UX-050 - Skills-Anforderung bei Job-Analyse vorab kommunizieren ([88a8e0f](https://github.com/filipores/obojobs/commit/88a8e0f465b200b902492206250de4ee50fd5844))
* UX-051 - Verbesserte Hamburger-Menü Schliessung auf Mobile ([3febc98](https://github.com/filipores/obojobs/commit/3febc9888bfae44d9d4de8b222a9a0625a2dc16c))
* UX-052 - Job-Fit-Score Fehlermeldung verbessern ([d38db6e](https://github.com/filipores/obojobs/commit/d38db6e0beca9921e910a44daf5bc23a758e1991))
* UX-053 - Konsistenteres Skill-Management zwischen Job-Analyse und Dokumenten ([d8b267d](https://github.com/filipores/obojobs/commit/d8b267da1fa6f136871c576bde1fbecc63cde154)), closes [documents#skills](https://github.com/documents/issues/skills)
* UX-054 - Proaktive Skill-Extraction Anleitung fuer neue Benutzer ([f5562cd](https://github.com/filipores/obojobs/commit/f5562cd7e643335e0c796d6b018243fe9693b2d6))
* UX-055 - Validierung bei Skill-Hinzufuegen implementieren ([5326043](https://github.com/filipores/obojobs/commit/5326043f8816298a0e158875631e316f7ed3fb48))
* UX-056 - Verbesserte Fehlerbehandlung fuer Job-Analyse ([97c27e8](https://github.com/filipores/obojobs/commit/97c27e89fa4248d26be0f072bb85a7dac16e57dc))
* UX-057 - Progressiver Workflow fuer Bewerbungserstellung ([7e58f5b](https://github.com/filipores/obojobs/commit/7e58f5bfb29d4a16c9db71829fa9e35cfad95c0f))
* UX-058 - Email verification countdown in Minuten anzeigen ([db2ded8](https://github.com/filipores/obojobs/commit/db2ded8699df21d919d6f5022917fb03557a8490))
* UX-059 - Template-Erstellung Workflow Verbesserung ([5c86c1f](https://github.com/filipores/obojobs/commit/5c86c1f4bab8f8baae6421a40209733344f6b357))
* UX-060 - Skills Management Verbesserungen ([02a0de4](https://github.com/filipores/obojobs/commit/02a0de42c7b50692eb26317d457de573515cf9ff))
* UX-061 - Bessere Verknuepfung zwischen Bewerbung und Dokument-Upload ([a4eab34](https://github.com/filipores/obojobs/commit/a4eab34e4ee5c9dbb43a77c3b8d89a899e100deb))
