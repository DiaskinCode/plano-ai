import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

interface Plan {
  id: string;
  name: string;
  priceMonthly: number;
  priceYearly: number;
  features: string[];
  isPopular?: boolean;
  color: string;
}

const PLANS: Plan[] = [
  {
    id: 'basic',
    name: 'Basic',
    priceMonthly: 25,
    priceYearly: 240,
    features: [
      'Full personalized plan',
      '200+ tasks',
      'Basic AI chat',
      'Community access',
      'Progress tracking',
    ],
    color: '#6366F1',
  },
  {
    id: 'pro',
    name: 'Pro',
    priceMonthly: 100,
    priceYearly: 960,
    features: [
      'Everything in Basic',
      'AI mentor assigned',
      'Priority support',
      'Essay feedback',
      'Weekly check-ins',
      'Application reviews',
    ],
    isPopular: true,
    color: '#F59E0B',
  },
  {
    id: 'premium',
    name: 'Premium',
    priceMonthly: 200,
    priceYearly: 1920,
    features: [
      'Everything in Pro',
      'Dedicated mentor',
      'Unlimited support',
      '24/7 response',
      'Video calls (4x/month)',
      'Application strategy',
    ],
    color: '#10B981',
  },
];

export default function SubscriptionScreen() {
  const router = useRouter();
  const { t } = useTranslation();

  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [selectedPlan, setSelectedPlan] = useState<string>('pro');

  const handlePlanSelect = (planId: string) => {
    setSelectedPlan(planId);
  };

  const handleContinue = () => {
    router.push('/(onboarding)/payment');
  };

  const handleSkip = () => {
    router.push('/(main)');
  };

  const getDisplayPrice = (plan: Plan) => {
    return billingCycle === 'monthly' ? plan.priceMonthly : plan.priceYearly;
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Progress */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: '78%' }]} />
          </View>
          <Text style={styles.progressText}>Step 12 of 14</Text>
        </View>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Choose Your Plan</Text>
          <Text style={styles.subtitle}>
            Unlock your full potential with the right plan
          </Text>
        </View>

        {/* Billing Toggle */}
        <View style={styles.billingToggle}>
          <TouchableOpacity
            style={[styles.billingButton, billingCycle === 'monthly' && styles.billingButtonActive]}
            onPress={() => setBillingCycle('monthly')}
          >
            <Text style={[styles.billingButtonText, billingCycle === 'monthly' && styles.billingButtonTextActive]}>
              Monthly
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.billingButton, billingCycle === 'yearly' && styles.billingButtonActive]}
            onPress={() => setBillingCycle('yearly')}
          >
            <Text style={[styles.billingButtonText, billingCycle === 'yearly' && styles.billingButtonTextActive]}>
              Yearly
            </Text>
            <View style={styles.saveBadge}>
              <Text style={styles.saveBadgeText}>Save 20%</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Plans */}
        <View style={styles.plansContainer}>
          {PLANS.map((plan) => {
            const isSelected = selectedPlan === plan.id;
            const price = getDisplayPrice(plan);

            return (
              <TouchableOpacity
                key={plan.id}
                style={[
                  styles.planCard,
                  isSelected && { borderColor: plan.color },
                  plan.isPopular && styles.planCardPopular,
                ]}
                onPress={() => handlePlanSelect(plan.id)}
                activeOpacity={0.7}
              >
                {plan.isPopular && (
                  <View style={[styles.popularBadge, { backgroundColor: plan.color }]}>
                    <Text style={styles.popularBadgeText}>Most Popular</Text>
                  </View>
                )}

                <View style={styles.planHeader}>
                  <Text style={styles.planName}>{plan.name}</Text>
                  {isSelected && (
                    <View style={[styles.checkIcon, { backgroundColor: plan.color }]}>
                      <Text style={styles.checkIconText}>✓</Text>
                    </View>
                  )}
                </View>

                <View style={styles.planPrice}>
                  <Text style={styles.planPriceValue}>${price}</Text>
                  <Text style={styles.planPricePeriod}>
                    /{billingCycle === 'monthly' ? 'month' : 'year'}
                  </Text>
                </View>

                {billingCycle === 'yearly' && (
                  <Text style={styles.planMonthlyEquivalent}>
                    ${(plan.priceYearly / 12).toFixed(0)}/month
                  </Text>
                )}

                <View style={styles.planFeatures}>
                  {plan.features.map((feature, index) => (
                    <View key={index} style={styles.featureItem}>
                      <Text style={styles.featureCheck}>✓</Text>
                      <Text style={styles.featureText}>{feature}</Text>
                    </View>
                  ))}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Special Offer */}
        <View style={styles.specialOffer}>
          <Text style={styles.specialOfferIcon}>🎉</Text>
          <View style={styles.specialOfferContent}>
            <Text style={styles.specialOfferTitle}>Special Offer</Text>
            <Text style={styles.specialOfferText}>
              Get 50% off your first month with code{' '}
              <Text style={styles.promoCode}>FIRST50</Text>
            </Text>
          </View>
        </View>

        {/* Security Badge */}
        <View style={styles.securityBadge}>
          <Text style={styles.securityIcon}>🔒</Text>
          <Text style={styles.securityText}>
            Secure payment powered by Stripe. Cancel anytime.
          </Text>
        </View>

        {/* Continue Button */}
        <TouchableOpacity
          style={styles.continueButton}
          onPress={handleContinue}
        >
          <Text style={styles.continueButtonText}>
            Continue with {PLANS.find(p => p.id === selectedPlan)?.name}
          </Text>
        </TouchableOpacity>

        {/* Skip Button */}
        <TouchableOpacity
          style={styles.skipButton}
          onPress={handleSkip}
        >
          <Text style={styles.skipButtonText}>Continue with Free Plan</Text>
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
  billingToggle: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    padding: 4,
    marginBottom: 32,
  },
  billingButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    position: 'relative',
  },
  billingButtonActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  billingButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#6B7280',
  },
  billingButtonTextActive: {
    color: '#111827',
    fontWeight: '600',
  },
  saveBadge: {
    position: 'absolute',
    top: -8,
    right: 4,
    backgroundColor: '#10B981',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  saveBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  plansContainer: {
    gap: 16,
    marginBottom: 24,
  },
  planCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 20,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    position: 'relative',
  },
  planCardPopular: {
    borderColor: '#F59E0B',
    backgroundColor: '#FFFBEB',
  },
  popularBadge: {
    position: 'absolute',
    top: -12,
    left: 20,
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  popularBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  planHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  planName: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111827',
  },
  checkIcon: {
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkIconText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  planPrice: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 4,
  },
  planPriceValue: {
    fontSize: 36,
    fontWeight: '700',
    color: '#111827',
  },
  planPricePeriod: {
    fontSize: 16,
    color: '#6B7280',
    marginLeft: 4,
  },
  planMonthlyEquivalent: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 20,
  },
  planFeatures: {
    gap: 12,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  featureCheck: {
    fontSize: 16,
    color: '#10B981',
  },
  featureText: {
    flex: 1,
    fontSize: 15,
    color: '#374151',
  },
  specialOffer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EEF2FF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    gap: 16,
  },
  specialOfferIcon: {
    fontSize: 28,
  },
  specialOfferContent: {
    flex: 1,
  },
  specialOfferTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4338CA',
    marginBottom: 4,
  },
  specialOfferText: {
    fontSize: 14,
    color: '#4338CA',
  },
  promoCode: {
    fontWeight: '600',
  },
  securityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 10,
    padding: 14,
    marginBottom: 24,
    gap: 12,
  },
  securityIcon: {
    fontSize: 18,
  },
  securityText: {
    flex: 1,
    fontSize: 13,
    color: '#6B7280',
  },
  continueButton: {
    backgroundColor: '#6366F1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  skipButton: {
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  skipButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#6B7280',
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
