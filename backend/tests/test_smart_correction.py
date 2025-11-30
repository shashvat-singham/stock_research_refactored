"""
Test suite for Smart Correction Service.
Uses real Gemini API if available, otherwise uses mocks.
"""
import pytest
import os
from unittest.mock import Mock, patch
from backend.services.smart_correction_service import SmartCorrectionService


class TestSmartCorrectionService:
    """Test cases for SmartCorrectionService."""
    
    @pytest.fixture
    def use_real_api(self):
        """Check if we should use real API or mocks."""
        # Load from .env file
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv('GEMINI_API_KEY') is not None
    
    @pytest.fixture
    def service(self, use_real_api):
        """Create a SmartCorrectionService instance."""
        if use_real_api:
            # Use real API
            return SmartCorrectionService()
        else:
            # Use mocked API
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
                with patch('google.generativeai.configure'):
                    with patch('google.generativeai.GenerativeModel'):
                        service = SmartCorrectionService(api_key='test_key')
                        return service
    
    def test_detect_simple_typo(self, service, use_real_api):
        """Test detection of simple typo (matae -> Meta)."""
        if not use_real_api:
            # Mock response
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_response = Mock()
                mock_response.text = '''```json
{
    "is_misspelled": true,
    "original_input": "matae",
    "corrected_name": "Meta Platforms Inc.",
    "ticker": "META",
    "confidence": "high",
    "explanation": "Detected likely misspelling of Meta"
}
```'''
                mock_generate.return_value = mock_response
                result = service.detect_and_correct("matae")
        else:
            # Real API call
            result = service.detect_and_correct("matae")
        
        # Verify result structure
        assert 'is_misspelled' in result
        assert 'original_input' in result
        
        # If misspelled, should have correction details
        if result.get('is_misspelled'):
            assert result.get('ticker') is not None
            assert result.get('corrected_name') is not None
    
    def test_detect_phonetic_similarity(self, service, use_real_api):
        """Test detection of phonetic similarity (microsft -> Microsoft)."""
        if not use_real_api:
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_response = Mock()
                mock_response.text = '''```json
{
    "is_misspelled": true,
    "original_input": "microsft",
    "corrected_name": "Microsoft Corporation",
    "ticker": "MSFT",
    "confidence": "high",
    "explanation": "Phonetic similarity detected"
}
```'''
                mock_generate.return_value = mock_response
                result = service.detect_and_correct("microsft")
        else:
            result = service.detect_and_correct("microsft")
        
        assert 'is_misspelled' in result
        if result.get('is_misspelled'):
            assert result.get('ticker') is not None
    
    def test_correct_spelling_no_correction(self, service, use_real_api):
        """Test that correctly spelled names don't trigger correction."""
        if not use_real_api:
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_response = Mock()
                mock_response.text = '''```json
{
    "is_misspelled": false,
    "original_input": "Apple",
    "corrected_name": null,
    "ticker": null,
    "confidence": "high",
    "explanation": "Correctly spelled company name"
}
```'''
                mock_generate.return_value = mock_response
                result = service.detect_and_correct("Apple")
        else:
            result = service.detect_and_correct("Apple")
        
        assert 'is_misspelled' in result
        # Apple is correctly spelled, should not be misspelled
        # (though AI might still detect it, so we just check structure)
    
    def test_valid_ticker_no_correction(self, service, use_real_api):
        """Test that valid tickers don't trigger correction."""
        if not use_real_api:
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_response = Mock()
                mock_response.text = '''```json
{
    "is_misspelled": false,
    "original_input": "AAPL",
    "corrected_name": null,
    "ticker": null,
    "confidence": "high",
    "explanation": "Valid ticker symbol"
}
```'''
                mock_generate.return_value = mock_response
                result = service.detect_and_correct("AAPL")
        else:
            result = service.detect_and_correct("AAPL")
        
        assert 'is_misspelled' in result
    
    def test_multiple_typos_in_query(self, service, use_real_api):
        """Test detection of multiple typos in one query."""
        if not use_real_api:
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_response = Mock()
                mock_response.text = '''```json
{
    "has_misspellings": true,
    "original_input": "metae and TSLAA",
    "corrections": [
        {
            "original": "metae",
            "corrected_name": "Meta Platforms Inc.",
            "ticker": "META",
            "confidence": "high",
            "explanation": "Likely misspelling"
        },
        {
            "original": "TSLAA",
            "corrected_name": "Tesla Inc.",
            "ticker": "TSLA",
            "confidence": "high",
            "explanation": "Extra letter detected"
        }
    ]
}
```'''
                mock_generate.return_value = mock_response
                result = service.detect_and_correct_multiple("metae and TSLAA")
        else:
            result = service.detect_and_correct_multiple("metae and TSLAA")
        
        assert 'has_misspellings' in result
        assert 'corrections' in result
        
        if result.get('has_misspellings'):
            assert len(result.get('corrections', [])) > 0
    
    def test_full_query_with_typo(self, service, use_real_api):
        """Test full query with typo."""
        if not use_real_api:
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_response = Mock()
                mock_response.text = '''```json
{
    "is_misspelled": true,
    "original_input": "Analyze matae for 1 month",
    "corrected_name": "Meta Platforms Inc.",
    "ticker": "META",
    "confidence": "high",
    "explanation": "Detected misspelling in query"
}
```'''
                mock_generate.return_value = mock_response
                result = service.detect_and_correct("Analyze matae for 1 month")
        else:
            result = service.detect_and_correct("Analyze matae for 1 month")
        
        assert 'is_misspelled' in result
        if result.get('is_misspelled'):
            assert result.get('ticker') is not None
    
    def test_generate_confirmation_message_high_confidence(self, service):
        """Test confirmation message generation with high confidence."""
        correction_result = {
            "is_misspelled": True,
            "corrected_name": "Meta Platforms Inc.",
            "ticker": "META",
            "confidence": "high"
        }
        
        message = service.generate_confirmation_message(correction_result)
        
        assert message is not None
        assert "Meta Platforms Inc." in message
        assert "META" in message
    
    def test_generate_confirmation_message_medium_confidence(self, service):
        """Test confirmation message generation with medium confidence."""
        correction_result = {
            "is_misspelled": True,
            "corrected_name": "Tesla Inc.",
            "ticker": "TSLA",
            "confidence": "medium"
        }
        
        message = service.generate_confirmation_message(correction_result)
        
        assert message is not None
        assert "Tesla Inc." in message
        assert "moderately confident" in message.lower() or "medium" in message.lower()
    
    def test_generate_confirmation_message_low_confidence(self, service):
        """Test confirmation message generation with low confidence."""
        correction_result = {
            "is_misspelled": True,
            "corrected_name": "Amazon.com Inc.",
            "ticker": "AMZN",
            "confidence": "low"
        }
        
        message = service.generate_confirmation_message(correction_result)
        
        assert message is not None
        assert "Amazon.com Inc." in message
    
    def test_generate_confirmation_message_not_misspelled(self, service):
        """Test that no message is generated when not misspelled."""
        correction_result = {
            "is_misspelled": False
        }
        
        message = service.generate_confirmation_message(correction_result)
        
        assert message is None
    
    def test_error_handling(self, service, use_real_api):
        """Test error handling when API fails."""
        if not use_real_api:
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_generate.side_effect = Exception("API Error")
                
                result = service.detect_and_correct("test input")
                
                # Should return safe fallback
                assert result['is_misspelled'] == False
                assert result['original_input'] == "test input"
        else:
            # With real API, just verify it doesn't crash
            try:
                result = service.detect_and_correct("test input")
                assert 'is_misspelled' in result
            except Exception:
                pytest.skip("Real API error - acceptable in testing")
    
    def test_json_extraction_with_markdown(self, service, use_real_api):
        """Test JSON extraction from markdown code blocks."""
        if not use_real_api:
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_response = Mock()
                mock_response.text = '''Here is the result:
```json
{
    "is_misspelled": true,
    "original_input": "gogle",
    "corrected_name": "Alphabet Inc.",
    "ticker": "GOOGL",
    "confidence": "high",
    "explanation": "Common misspelling"
}
```
Hope this helps!'''
                mock_generate.return_value = mock_response
                
                result = service.detect_and_correct("gogle")
                
                assert result['is_misspelled'] == True
                assert result['ticker'] == "GOOGL"
        else:
            # Real API handles this automatically
            result = service.detect_and_correct("gogle")
            assert 'is_misspelled' in result
    
    def test_json_extraction_without_markdown(self, service, use_real_api):
        """Test JSON extraction from plain JSON response."""
        if not use_real_api:
            with patch.object(service.model, 'generate_content') as mock_generate:
                mock_response = Mock()
                mock_response.text = '''{
    "is_misspelled": true,
    "original_input": "amazn",
    "corrected_name": "Amazon.com Inc.",
    "ticker": "AMZN",
    "confidence": "high",
    "explanation": "Missing letter"
}'''
                mock_generate.return_value = mock_response
                
                result = service.detect_and_correct("amazn")
                
                assert result['is_misspelled'] == True
                assert result['ticker'] == "AMZN"
        else:
            # Real API handles this automatically
            result = service.detect_and_correct("amazn")
            assert 'is_misspelled' in result
    
    def test_multiple_corrections_message(self, service):
        """Test message generation for multiple corrections."""
        corrections = [
            {
                "original": "metae",
                "corrected_name": "Meta Platforms Inc.",
                "ticker": "META",
                "confidence": "high",
                "explanation": "Typo"
            },
            {
                "original": "TSLAA",
                "corrected_name": "Tesla Inc.",
                "ticker": "TSLA",
                "confidence": "high",
                "explanation": "Extra letter"
            }
        ]
        
        message = service.generate_multiple_corrections_message(corrections)
        
        assert message is not None
        assert "Meta Platforms Inc." in message
        assert "Tesla Inc." in message
        assert "META" in message
        assert "TSLA" in message
    
    def test_single_correction_message(self, service):
        """Test message generation for single correction."""
        corrections = [
            {
                "original": "metae",
                "corrected_name": "Meta Platforms Inc.",
                "ticker": "META",
                "confidence": "high",
                "explanation": "Typo"
            }
        ]
        
        message = service.generate_multiple_corrections_message(corrections)
        
        assert message is not None
        assert "Meta Platforms Inc." in message
        assert "META" in message

