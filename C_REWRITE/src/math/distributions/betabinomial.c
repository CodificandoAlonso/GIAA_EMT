#include <math.h>
#include <stdbool.h>
#include "math/math_utils.h"
#include "math/distributions/generic/generic_distro.h"





double aux_sample_binomial(
    u32 N, double p, RNG *random_gen
){





    if (p <= 0.0 || p > 1.0) return 0.0;


    if (p > 0.5) {
        return (double)N - aux_sample_binomial(N, (1 - p), random_gen);
    }


    // ASsign q = 1 - p.
    double q = 1 - p;


    double s = p / q;

    double a = (N + 1)*s;

    double r = pow(q, N);

    if (r <= 0.0){
        //WIth central limit theorem, in this case, it converges to a Normal

        double mu = N * p;

        double sigma = sqrt(mu*(1 - p));

        uint32_t new_gen = pcg32_random_r(random_gen);

        double u1 = rng_uniform(new_gen);

        new_gen = pcg32_random_r(random_gen);

        double u2 = rng_uniform(new_gen);

        double Z = sqrt(-2*log(u1))*cos(2*PI*u2);

        return round(mu + sigma*Z);
    }


    //OBtain u ~ U(0,1)
    uint32_t new_gen = pcg32_random_r(random_gen);

    double u = rng_uniform(new_gen);

    double x = 0;
    const double max_x = (double)N;
    while (u > r && x < max_x){

        u = u -r;
        x += 1.0;

        r = ((a /x) -s)*r;

        if (r <= 0.0) break;
    }
    return x;

}












/**
 * @brief Samples a random value from a negative binomial distribution
 *        using a Gamma-Poisson mixture.
 *
 * @param betabinomial_distribution Pointer to the negative binomial
 *                            distribution structure.
 * @param random_gen Pointer to the RNG structure.
 *
 * @return The sampled uint32 value.
 */
double sample_betabinomial(
    void *parameters
){

    distribution_sampling_parameters *betabinomial_params = parameters;

    distribution *betabinomial_distro = betabinomial_params->self;

    RNG *random_gen = betabinomial_params->random_gen;

    u32 N = betabinomial_params->N;

    //Using the Generating Beta
    // Variates with Nonintegral Shape Parameters
    // R. C. H. Cheng
    // University of Wales Institute of Science and Technology

    //There are two approaches, BB's algorithm and BC's algorithm.

    int decision = 0;

    if (min(betabinomial_distro->value1, betabinomial_distro->value2) > 1){
        decision = 0;
    }else{
        decision = 1;
    }

    double p = 0.0;

    switch (decision){

        case 0:{
            //BB

            double a = min(betabinomial_distro->value1, betabinomial_distro->value2);
            double b = max(betabinomial_distro->value1, betabinomial_distro->value2);

            double alpha = a + b;

            double beta = sqrt((alpha -2)/ (2*a*b - alpha));

            double gamma = a + 1/beta;


            double v, w, z, r, s = 0.0;

            loop_bb:{
                //SAmple 2 ues.
                uint32_t new_gen = pcg32_random_r(random_gen);

                double u1 = rng_uniform(new_gen);

                new_gen = pcg32_random_r(random_gen);

                double u2 = rng_uniform(new_gen);

                //V =beta * log{U1/(1 - U1)}
                v = beta * log(u1 / (1 - u1));

                w = a*exp( v);

                z = pow(u1, 2)*u2;

                r = gamma*v -log(4);

                s = a + r - w;

                if (s + 2.609438 >= 5*z) goto finish;

                double t = log(z);
                
                if (s >= t) goto finish;

                if (r + alpha * log(alpha/(b + w)) < t){
                    goto loop_bb;
                }
                else{
                    goto finish;
                }
            }

            finish:{
                if (a == betabinomial_distro->value1){
                    p = w /(b + w);
                }else{
                    p = b/(b + w);
                }

            }
        break;
        }
        case 1:{
            //BC


            // A l g o r i t h m B C (rnin(ao, bo) <- 1)
            // Initialization: Set a = max (a0, b0); b = min (a0, b0); a
            // = a + b ; /3 = b - ~ ; 8 = 1 + a - b ; KI =
            // 8(0.0138889+0.0416667b)/(a/3-0.777778); Kz = 0.25
            // + (0.5+0.258-~)b. (Here K1 = kl/4, K2 = k2/4.)
            // 1. Generate random numbers Ui, Uz, and if U1 --- ½ go
            // to 3.
            // 2. S e t Y = U~ U2, Z = UI Y. If O.25 U2 + Z - Y >- K~,
            // go to 1; otherwise go to 5.
            // 3. Set Z = U21Uz. If Z --- 0.25, set V =
            // /3 log { U 1 / ( 1 - U 1 ) } , W = ae v, and go to 6.
            // 4. If Z_> K2 go to 1.
            // 5. Set V = /3 log { U I / ( 1 - U 1 ) } , W = ae v. If
            // a{log [ a / ( b + W ) ] + V} - 1.3862944 < log Z, go
            // to 1.
            // 6. If a = a0 deliver X = W / ( b + W ) ; otherwise deliver
            // X = b / ( b + W ) .
            
            double a = max(betabinomial_distro->value1, betabinomial_distro->value2);
            double b = min(betabinomial_distro->value1, betabinomial_distro->value2);

            double alpha = a + b;

            double beta = 1 / b;

            double gamma = 1 + a - b;

            double k1 = gamma*(0.0138889 + 0.041667*b)/(a*beta - 0.777778);

            double k2 = 0.25 + (0.5 + 0.25*(1/gamma))*b;

            double u1,u2, y,z,v,w = 0.0;

            step_one_init: {

                //Sample RNG numbers.
                //SAmple 2 ues.
                uint32_t new_gen = pcg32_random_r(random_gen);

                u1 = rng_uniform(new_gen);

                new_gen = pcg32_random_r(random_gen);

                u2 = rng_uniform(new_gen);

                if (u1 >= 0.5)goto step_three;


                y = u1*u2;
                z = u1*y;

                if (0.25*u2 + z - y >= k1){goto step_one_init;}
                else{goto step_five;}


                step_three:{
                    z = pow(u1,2)*u2;

                    if (z <= 0.25){
                        v = beta * log(u1/(1- u1));
                        w = a* exp(v);
                        goto step_six;
                    }
                    if ( z >=k2){goto step_one_init;}
                    else{goto step_five;}

                }

                step_five:{
                    v = beta * log(u1/(1- u1));
                    w = a* exp(v);

                    if (alpha*(log((alpha/(b + w))) + v) -1.3862944 < log(z)){
                        goto step_one_init;
                    }else{
                        goto step_six;
                    }
                }
                step_six:{

                    if (a == betabinomial_distro->value1){
                        p = w/(b + w);
                    }else{
                        p = b/(b + w);
                    }
                }
            }
        }
    }


    //NOw after obtaining p, i can draw the sampling by simply using the binomial 
    // sampling. I will call an auxiliar function that use
    //the same method than sample_binomial. Difference is that i skip the overhead 
    // of building a distribution to parse the aprameters into the funciton

    double X = aux_sample_binomial(N, p, random_gen);

    return X;
}