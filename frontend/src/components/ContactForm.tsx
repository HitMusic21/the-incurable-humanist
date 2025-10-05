import Card from "./Card";
import PillButton from "./PillButton";
import { useForm, ValidationError } from '@formspree/react';
import { useEffect, useRef } from 'react';
import { useAnalytics } from '@/hooks/useAnalytics';

export default function ContactForm() {
  const [state, handleSubmit] = useForm("xldplgoz");
  const formRef = useRef<HTMLFormElement>(null);
  const { track, identify, events } = useAnalytics();

  // Reset form after successful submission and track success
  useEffect(() => {
    if (state.succeeded && formRef.current) {
      // Get form data for tracking
      const formData = new FormData(formRef.current);
      const name = formData.get('name') as string;
      const email = formData.get('email') as string;
      const subject = formData.get('subject') as string;

      // Identify user with their email
      if (email) {
        identify(email, {
          name,
          email,
          contact_method: 'contact_form',
          timestamp: new Date().toISOString(),
        });
      }

      // Track successful form submission
      track(events.CONTACT_FORM_SUBMIT, {
        name,
        email,
        subject: subject || 'No subject',
        has_subject: Boolean(subject),
      });

      formRef.current.reset();
    }
  }, [state.succeeded, track, identify, events]);

  // If submission succeeded, show success message
  if (state.succeeded) {
    return (
      <Card className="p-6 md:p-8">
        <div className="text-center py-8">
          <div className="mb-6">
            <svg className="w-16 h-16 mx-auto text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="font-serif text-accent2 text-[24px] md:text-[28px] mb-4">
            Message Sent!
          </h3>
          <p className="text-[17px] md:text-[18px] text-muted-ink mb-8">
            Thank you for reaching out. I'll get back to you as soon as possible.
          </p>
          <PillButton as="button" onClick={() => window.location.reload()}>
            Send Another Message
          </PillButton>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 md:p-8">
      <h2 className="font-serif text-[24px] text-ink mb-6">Send a Message</h2>

      <form 
        ref={formRef} 
        onSubmit={(e) => {
          // Track form submission attempt
          track(events.CONTACT_FORM_SUBMIT, {
            form_started: true,
          });
          
          // Track errors if form fails validation
          if (state.errors && state.errors.length > 0) {
            track(events.CONTACT_FORM_ERROR, {
              errors: state.errors.map(error => error.message),
            });
          }
          
          handleSubmit(e);
        }}
      >
        <div className="mb-6">
          <label htmlFor="contact-name" className="block text-[15px] font-medium mb-2">
            Name <span className="text-accent">*</span>
          </label>
          <input
            id="contact-name"
            name="name"
            required
            aria-required="true"
            autoComplete="name"
            className="w-full rounded-xl border border-line bg-white h-12 px-4 outline-none transition-all duration-200 focus:ring-2 focus:ring-accent/30 focus:border-accent hover:border-accent/30"
          />
        </div>

        <div className="mb-6">
          <label htmlFor="contact-email" className="block text-[15px] font-medium mb-2">
            Email <span className="text-accent">*</span>
          </label>
          <input
            id="contact-email"
            name="email"
            type="email"
            required
            aria-required="true"
            autoComplete="email"
            className="w-full rounded-xl border border-line bg-white h-12 px-4 outline-none transition-all duration-200 focus:ring-2 focus:ring-accent/30 focus:border-accent hover:border-accent/30"
          />
        </div>

        <div className="mb-6">
          <label htmlFor="contact-subject" className="block text-[15px] font-medium mb-2">
            Subject
          </label>
          <input
            id="contact-subject"
            name="subject"
            autoComplete="off"
            className="w-full rounded-xl border border-line bg-white h-12 px-4 outline-none transition-all duration-200 focus:ring-2 focus:ring-accent/30 focus:border-accent hover:border-accent/30"
          />
        </div>

        <div className="mb-8">
          <label htmlFor="contact-message" className="block text-[15px] font-medium mb-2">
            Message <span className="text-accent">*</span>
          </label>
          <textarea
            id="contact-message"
            name="message"
            required
            aria-required="true"
            className="w-full rounded-xl border border-line bg-white min-h-[180px] p-4 outline-none resize-none transition-all duration-200 focus:ring-2 focus:ring-accent/30 focus:border-accent hover:border-accent/30"
          />
        </div>

        <PillButton as="button" type="submit" disabled={state.submitting}>
          {state.submitting ? 'Sending...' : 'Send Message'}
        </PillButton>

        {state.succeeded && (
          <p className="mt-4 text-[15px] text-accent" role="alert">
            Message sent! I'll reply soon.
          </p>
        )}
        <ValidationError
          prefix="Email"
          field="email"
          errors={state.errors}
          className="mt-2 text-[14px] text-red-600"
        />
        <ValidationError
          prefix="Message"
          field="message"
          errors={state.errors}
          className="mt-2 text-[14px] text-red-600"
        />
      </form>
    </Card>
  );
}
