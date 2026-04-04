import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
	vus: 50,          // 50 concurrent users
	duration: '30s',  // run for 30 seconds
};

export default function() {
	// Test the health endpoint
	const healthRes = http.get('http://localhost:5000/health');
	check(healthRes, {
		'health status is 200': (r) => r.status === 200,
	});

	// Test shortening a URL
	const shortenRes = http.post(
		'http://localhost:5000/shorten',
		JSON.stringify({ url: 'https://google.com' }),
		{ headers: { 'Content-Type': 'application/json' } }
	);
	check(shortenRes, {
		'shorten status is 201': (r) => r.status === 201,
	});

}
