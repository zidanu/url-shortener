import http from 'k6/http';
import { check } from 'k6';

export const options = {
	vus: 200,         // 200 concurrent users
	duration: '30s',
};

export default function() {
	const healthRes = http.get('http://localhost:8080/health');
	check(healthRes, {
		'health status is 200': (r) => r.status === 200,
	});

	const shortenRes = http.post(
		'http://localhost:8080/shorten',
		JSON.stringify({ url: 'https://google.com' }),
		{ headers: { 'Content-Type': 'application/json' } }
	);
	check(shortenRes, {
		'shorten status is 201': (r) => r.status === 201,
	});
}
