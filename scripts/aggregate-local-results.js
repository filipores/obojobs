#!/usr/bin/env node
/**
 * Aggregates local CI results into a JSON format compatible with GitHub CI
 *
 * Usage: node aggregate-local-results.js <results-dir>
 *
 * Reads individual step results from <results-dir>/*.json
 * Writes aggregated results to <results-dir>/ci-results.json
 */

const fs = require('fs');
const path = require('path');

const resultsDir = process.argv[2] || '.ci-results';

if (!fs.existsSync(resultsDir)) {
    console.error(`Results directory not found: ${resultsDir}`);
    process.exit(1);
}

// Read all individual result files
const resultFiles = fs.readdirSync(resultsDir)
    .filter(f => f.endsWith('.json') && f !== 'ci-results.json');

const steps = [];
const jobs = {};

for (const file of resultFiles) {
    try {
        const content = fs.readFileSync(path.join(resultsDir, file), 'utf8');
        const result = JSON.parse(content);
        steps.push(result);

        // Group by job
        if (!jobs[result.job]) {
            jobs[result.job] = {
                name: result.job,
                status: 'success',
                steps: [],
                duration_ms: 0,
                started_at: result.timestamp,
                completed_at: result.timestamp
            };
        }
        jobs[result.job].steps.push({
            name: result.step,
            status: result.status,
            duration_ms: result.duration_ms,
            output: result.output
        });
        jobs[result.job].duration_ms += result.duration_ms;
        if (result.status === 'failure') {
            jobs[result.job].status = 'failure';
        }
    } catch (err) {
        console.error(`Error reading ${file}: ${err.message}`);
    }
}

// Calculate overall status
const overallStatus = Object.values(jobs).some(j => j.status === 'failure')
    ? 'failure'
    : 'success';

const totalDuration = Object.values(jobs).reduce((sum, j) => sum + j.duration_ms, 0);

// Build final result structure (GitHub Actions compatible format)
const aggregatedResult = {
    workflow_run: {
        id: `local-${Date.now()}`,
        name: 'CI (Local)',
        status: 'completed',
        conclusion: overallStatus,
        run_started_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        run_attempt: 1,
        head_branch: getGitBranch(),
        head_sha: getGitCommit(),
        event: 'local'
    },
    jobs: Object.values(jobs).map(job => ({
        id: `local-${job.name}`,
        name: job.name,
        status: 'completed',
        conclusion: job.status,
        started_at: job.started_at,
        completed_at: job.completed_at,
        steps: job.steps.map((step, i) => ({
            number: i + 1,
            name: step.name,
            status: 'completed',
            conclusion: step.status,
            duration_ms: step.duration_ms
        }))
    })),
    summary: {
        total_jobs: Object.keys(jobs).length,
        successful_jobs: Object.values(jobs).filter(j => j.status === 'success').length,
        failed_jobs: Object.values(jobs).filter(j => j.status === 'failure').length,
        total_steps: steps.length,
        successful_steps: steps.filter(s => s.status === 'success').length,
        failed_steps: steps.filter(s => s.status === 'failure').length,
        total_duration_ms: totalDuration,
        conclusion: overallStatus
    }
};

// Write aggregated result
const outputPath = path.join(resultsDir, 'ci-results.json');
fs.writeFileSync(outputPath, JSON.stringify(aggregatedResult, null, 2));

// Print summary
console.log('');
console.log('CI Results Summary:');
console.log(`  Status: ${overallStatus}`);
console.log(`  Jobs: ${aggregatedResult.summary.successful_jobs}/${aggregatedResult.summary.total_jobs} passed`);
console.log(`  Steps: ${aggregatedResult.summary.successful_steps}/${aggregatedResult.summary.total_steps} passed`);
console.log(`  Duration: ${(totalDuration / 1000).toFixed(1)}s`);

// Print failed steps if any
const failedSteps = steps.filter(s => s.status === 'failure');
if (failedSteps.length > 0) {
    console.log('');
    console.log('Failed steps:');
    for (const step of failedSteps) {
        console.log(`  - ${step.job}/${step.step}`);
    }
}

// Helper functions
function getGitBranch() {
    try {
        const { execSync } = require('child_process');
        return execSync('git branch --show-current', { encoding: 'utf8' }).trim();
    } catch {
        return 'unknown';
    }
}

function getGitCommit() {
    try {
        const { execSync } = require('child_process');
        return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
    } catch {
        return 'unknown';
    }
}
