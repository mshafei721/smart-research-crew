import React from "react";
import { motion } from "framer-motion";
import { File, TrendingUp, Monitor } from "lucide-react";

interface LandingPageProps {
  onGetStarted: () => void;
}

export default function LandingPage({ onGetStarted }: LandingPageProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col max-w-[960px] flex-1"
    >
      {/* Hero Section */}
      <div className="@container">
        <div className="@[480px]:p-4">
          <div
            className="flex min-h-[480px] flex-col gap-6 bg-cover bg-center bg-no-repeat @[480px]:gap-8 @[480px]:rounded-lg items-center justify-center p-4"
            style={{
              backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%), url("https://lh3.googleusercontent.com/aida-public/AB6AXuCLLV0uYAgF86Cy9COlOegREPFAoMgZ8FNuS_okMgrCJWGFskvJO1VWivS1I2R1GuAynh-6DzBStfPXBK_GPVOE0lpE0qcB-2wnsE8uZyHv8QmLew-7NO4aG_5lwieKKeAEFBs-m5AFXBhwkjhuhvM_U0LD5Sa603mWrvME8nUlsth9n77Ml6FrPa2h4JvVq4xw2Plcchrl5CU15ENVLanJoOr1Q9_2je1Y4UyY0Z7P1i1rUOMS0bpyhzE1wN--LHPejMWO8eu2NdQ")`,
            }}
          >
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="flex flex-col gap-2 text-center"
            >
              <h1 className="text-white text-4xl font-black leading-tight tracking-[-0.033em] @[480px]:text-5xl @[480px]:font-black @[480px]:leading-tight @[480px]:tracking-[-0.033em]">
                Generate Research Reports Effortlessly
              </h1>
              <h2 className="text-white text-sm font-normal leading-normal @[480px]:text-base @[480px]:font-normal @[480px]:leading-normal">
                Transform your research into polished, insightful reports with
                our intuitive web application. Streamline your workflow and
                focus on what matters most: your findings.
              </h2>
            </motion.div>
            <motion.button
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onGetStarted}
              className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-10 px-4 @[480px]:h-12 @[480px]:px-5 bg-[#357dc9] text-gray-50 text-sm font-bold leading-normal tracking-[0.015em] @[480px]:text-base @[480px]:font-bold @[480px]:leading-normal @[480px]:tracking-[0.015em]"
            >
              <span className="truncate">Get Started</span>
            </motion.button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <motion.div
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="flex flex-col gap-10 px-4 py-10 @container"
      >
        <div className="flex flex-col gap-4">
          <h1 className="text-[#101419] tracking-light text-[32px] font-bold leading-tight @[480px]:text-4xl @[480px]:font-black @[480px]:leading-tight @[480px]:tracking-[-0.033em] max-w-[720px]">
            Key Features
          </h1>
          <p className="text-[#101419] text-base font-normal leading-normal max-w-[720px]">
            Explore the powerful features designed to enhance your research
            reporting process.
          </p>
        </div>

        <div className="grid grid-cols-[repeat(auto-fit,minmax(158px,1fr))] gap-3 p-0">
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="flex flex-1 gap-3 rounded-lg border border-[#d3dbe4] bg-gray-50 p-4 flex-col"
          >
            <div className="text-[#101419]">
              <File size={24} />
            </div>
            <div className="flex flex-col gap-1">
              <h2 className="text-[#101419] text-base font-bold leading-tight">
                Automated Report Generation
              </h2>
              <p className="text-[#58728d] text-sm font-normal leading-normal">
                Generate comprehensive reports from your research data with just
                a few clicks.
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1.0 }}
            className="flex flex-1 gap-3 rounded-lg border border-[#d3dbe4] bg-gray-50 p-4 flex-col"
          >
            <div className="text-[#101419]">
              <TrendingUp size={24} />
            </div>
            <div className="flex flex-col gap-1">
              <h2 className="text-[#101419] text-base font-bold leading-tight">
                Data Visualization
              </h2>
              <p className="text-[#58728d] text-sm font-normal leading-normal">
                Visualize your data with interactive charts and graphs to
                enhance understanding.
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="flex flex-1 gap-3 rounded-lg border border-[#d3dbe4] bg-gray-50 p-4 flex-col"
          >
            <div className="text-[#101419]">
              <Monitor size={24} />
            </div>
            <div className="flex flex-col gap-1">
              <h2 className="text-[#101419] text-base font-bold leading-tight">
                Customizable Templates
              </h2>
              <p className="text-[#58728d] text-sm font-normal leading-normal">
                Choose from a variety of templates or create your own to match
                your brand and style.
              </p>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </motion.div>
  );
}
