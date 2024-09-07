import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Paper, Box } from '@mui/material';

const App = () => {
  const [text, setText] = useState('');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSummarize = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:3001/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      // Assuming the response contains { summary_text: '...' }
      setSummary(data.summary_text || '');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" gutterBottom>
          AI Text Summarizer
        </Typography>
        <Paper elevation={3} sx={{ padding: 2 }}>
          <TextField
            fullWidth
            multiline
            rows={6}
            variant="outlined"
            label="Enter text here"
            value={text}
            onChange={(e) => setText(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={handleSummarize}
            disabled={loading}
          >
            {loading ? 'Summarizing...' : 'Summarize'}
          </Button>
          {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
          {summary && (
            <Box sx={{ mt: 2, p: 2, border: '1px solid #ddd', borderRadius: '4px' }}>
              <Typography variant="h6">Summary:</Typography>
              <Typography>{summary}</Typography>
            </Box>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default App;
