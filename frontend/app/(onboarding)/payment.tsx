import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

export default function PaymentScreen() {
  const router = useRouter();
  const { t } = useTranslation();

  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvc, setCvc] = useState('');
  const [name, setName] = useState('');
  const [promoCode, setPromoCode] = useState('');
  const [saveCard, setSaveCard] = useState(true);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [loading, setLoading] = useState(false);

  const formatCardNumber = (text: string) => {
    const cleaned = text.replace(/\s/g, '').replace(/[^0-9]/gi, '');
    const formatted = cleaned.match(/.{1,4}/g)?.join(' ') || cleaned;
    return formatted.substring(0, 19);
  };

  const formatExpiry = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    if (cleaned.length >= 2) {
      return cleaned.substring(0, 2) + '/' + cleaned.substring(2, 4);
    }
    return cleaned;
  };

  const handlePay = async () => {
    // Validation
    if (cardNumber.replace(/\s/g, '').length !== 16) {
      Alert.alert('Invalid Card', 'Please enter a valid card number');
      return;
    }

    if (expiry.length !== 5) {
      Alert.alert('Invalid Expiry', 'Please enter a valid expiry date (MM/YY)');
      return;
    }

    if (cvc.length < 3) {
      Alert.alert('Invalid CVC', 'Please enter a valid CVC');
      return;
    }

    if (!name || name.trim().length < 2) {
      Alert.alert('Invalid Name', 'Please enter the cardholder name');
      return;
    }

    if (!agreedToTerms) {
      Alert.alert('Terms Required', 'Please agree to the Terms of Service');
      return;
    }

    try {
      setLoading(true);

      // TODO: Integrate Stripe payment
      // For now, simulate payment success

      await new Promise(resolve => setTimeout(resolve, 2000));

      router.push('/(onboarding)/success');
    } catch (error: any) {
      Alert.alert('Payment Error', error.message || 'Payment failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Progress */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: '85%' }]} />
          </View>
          <Text style={styles.progressText}>Step 13 of 14</Text>
        </View>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Payment Details</Text>
          <Text style={styles.subtitle}>
            Complete your subscription securely
          </Text>
        </View>

        {/* Order Summary */}
        <View style={styles.orderSummary}>
          <Text style={styles.summaryTitle}>Order Summary</Text>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Pro Plan (Monthly)</Text>
            <Text style={styles.summaryValue}>$100.00</Text>
          </View>
          {promoCode.toUpperCase() === 'FIRST50' && (
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabelDiscount}>First Month 50% Off</Text>
              <Text style={styles.summaryValueDiscount}>-$50.00</Text>
            </View>
          )}
          <View style={styles.summaryDivider} />
          <View style={styles.summaryRow}>
            <Text style={styles.summaryTotal}>Total Due Today</Text>
            <Text style={styles.summaryTotalValue}>
              ${promoCode.toUpperCase() === 'FIRST50' ? '50.00' : '100.00'}
            </Text>
          </View>
        </View>

        {/* Payment Methods */}
        <View style={styles.paymentMethods}>
          <Text style={styles.sectionTitle}>Payment Method</Text>
          <View style={styles.paymentButtons}>
            <TouchableOpacity style={[styles.paymentButton, styles.paymentButtonActive]}>
              <Text style={styles.paymentButtonText}>💳 Card</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.paymentButton}>
              <Text style={styles.paymentButtonText}>🍎 Apple Pay</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.paymentButton}>
              <Text style={styles.paymentButtonText}>🔵 PayPal</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Card Details Form */}
        <View style={styles.form}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Card Number</Text>
            <TextInput
              style={styles.input}
              placeholder="1234 5678 9012 3456"
              value={cardNumber}
              onChangeText={setCardNumber}
              keyboardType="number-pad"
              maxLength={19}
            />
          </View>

          <View style={styles.row}>
            <View style={[styles.inputGroup, styles.half]}>
              <Text style={styles.label}>Expiry Date</Text>
              <TextInput
                style={styles.input}
                placeholder="MM/YY"
                value={expiry}
                onChangeText={setExpiry}
                keyboardType="number-pad"
                maxLength={5}
              />
            </View>
            <View style={[styles.inputGroup, styles.half]}>
              <Text style={styles.label}>CVC</Text>
              <TextInput
                style={styles.input}
                placeholder="123"
                value={cvc}
                onChangeText={setCvc}
                keyboardType="number-pad"
                maxLength={4}
              />
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Cardholder Name</Text>
            <TextInput
              style={styles.input}
              placeholder="John Doe"
              value={name}
              onChangeText={setName}
              autoCapitalize="words"
            />
          </View>

          {/* Promo Code */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Promo Code (Optional)</Text>
            <View style={styles.promoRow}>
              <TextInput
                style={styles.promoInput}
                placeholder="Enter code"
                value={promoCode}
                onChangeText={setPromoCode}
                autoCapitalize="characters"
              />
              <TouchableOpacity style={styles.applyButton}>
                <Text style={styles.applyButtonText}>Apply</Text>
              </TouchableOpacity>
            </View>
            {promoCode.toUpperCase() === 'FIRST50' && (
              <Text style={styles.promoSuccess}>✓ Promo applied: 50% off first month</Text>
            )}
          </View>

          {/* Save Card */}
          <TouchableOpacity
            style={styles.toggle}
            onPress={() => setSaveCard(!saveCard)}
          >
            <View style={[styles.checkbox, saveCard && styles.checkboxChecked]}>
              {saveCard && <Text style={styles.checkmark}>✓</Text>}
            </View>
            <Text style={styles.toggleLabel}>Save card for future payments</Text>
          </TouchableOpacity>

          {/* Terms */}
          <TouchableOpacity
            style={styles.toggle}
            onPress={() => setAgreedToTerms(!agreedToTerms)}
          >
            <View style={[styles.checkbox, agreedToTerms && styles.checkboxChecked]}>
              {agreedToTerms && <Text style={styles.checkmark}>✓</Text>}
            </View>
            <Text style={styles.toggleLabel}>
              I agree to the{' '}
              <Text style={styles.link}>Terms of Service</Text>
              {' '}and{' '}
              <Text style={styles.link}>Privacy Policy</Text>
            </Text>
          </TouchableOpacity>
        </View>

        {/* Pay Button */}
        <TouchableOpacity
          style={[styles.payButton, loading && styles.payButtonDisabled]}
          onPress={handlePay}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.payButtonText}>
              Pay ${promoCode.toUpperCase() === 'FIRST50' ? '50.00' : '100.00'}
            </Text>
          )}
        </TouchableOpacity>

        {/* Back Button */}
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingTop: 20,
    paddingBottom: 24,
  },
  progressContainer: {
    marginBottom: 24,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#6366F1',
  },
  progressText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
  },
  orderSummary: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  summaryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#374151',
  },
  summaryLabelDiscount: {
    fontSize: 14,
    color: '#10B981',
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  summaryValueDiscount: {
    fontSize: 14,
    fontWeight: '500',
    color: '#10B981',
  },
  summaryDivider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 12,
  },
  summaryTotal: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
  },
  summaryTotalValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
  },
  paymentMethods: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  paymentButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  paymentButton: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  paymentButtonActive: {
    backgroundColor: '#EEF2FF',
    borderColor: '#6366F1',
  },
  paymentButtonText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#374151',
  },
  form: {
    marginBottom: 24,
    gap: 16,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  half: {
    flex: 1,
  },
  promoRow: {
    flexDirection: 'row',
    gap: 8,
  },
  promoInput: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    textTransform: 'uppercase',
  },
  applyButton: {
    backgroundColor: '#6366F1',
    borderRadius: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  applyButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  promoSuccess: {
    fontSize: 13,
    color: '#10B981',
  },
  toggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  checkmark: {
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  toggleLabel: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
  },
  link: {
    color: '#6366F1',
    fontWeight: '500',
  },
  payButton: {
    backgroundColor: '#6366F1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  payButtonDisabled: {
    opacity: 0.6,
  },
  payButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  backButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
