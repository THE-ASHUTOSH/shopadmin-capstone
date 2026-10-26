# ShopAdmin: demo video script

Narrated in first person by Ashutosh. Target length: about 7 minutes.
Each scene lists what is on screen, then what is said.

---

## 1. Opening
**On screen:** Slide 1, title

Hi, I'm Ashutosh, and this is ShopAdmin.

I'll start with a small confession. The app you're about to see is pretty simple, and that's on purpose. The real story of this project isn't the app. It's everything that happens after I hit save. My code gets checked, packed, shipped to the cloud, and then watched, all without me touching anything. Let me show you how.

## 2. Meet ShopAdmin
**On screen:** Slide 2

Picture someone running a small online shop. They need one place to keep track of their stock. ShopAdmin does three things for them. It lets them add and edit products. It shows what's running low. And it helps them find anything fast.

Under the hood it's a React website, a Python API built with FastAPI, and a PostgreSQL database.

## 3. The app, live
**On screen:** The real app running on my laptop with docker compose

Here it is, running on my laptop right now. Up top there are four cards: total products, low stock, categories, and the value of everything in the inventory.

Let's add something. I click "Add product" and fill in a wireless mouse with a SKU, a category, a price and forty in stock. I hit save, and it shows up in the table straight away. The cards at the top update on their own.

Now, what if I make a mistake and reuse a SKU that already exists? The API catches it, and the form tells me right there instead of quietly saving a duplicate.

Say we've sold most of our keyboards. I edit the stock down to six, and it turns orange. That's the low-stock warning, and the counter at the top goes up too.

Search is instant. I can type a name or a SKU, or filter by category. And if something gets discontinued, one click on delete and it's gone.

For developers, the API documents itself. This is the Swagger page FastAPI generates for free.

## 4. The problem
**On screen:** Slide 3

I could have built this, copied it onto a server by hand, and called it done. But releasing by hand has three problems.

First, it's slow. Every update means the same steps, over and over. Second, it's easy to slip. Skip one check and a bug reaches real users. And third, there's the classic line: "but it works on my laptop!" Then it breaks somewhere else.

So I decided to let the computer do the routine work.

## 5. The big picture
**On screen:** Slide 4

Here's the whole idea on one slide. I make a change and push it to GitHub. GitHub Actions picks it up and runs the tests and a security scan. Docker packs the app into containers. Kubernetes runs them in the cloud. And Prometheus and Grafana let me keep an eye on it.

There are no buttons to click. It takes about three minutes, every single time.

## 6. Checked before it goes live
**On screen:** Slide 5, then pytest output, then the Trivy scan in CI

Step one: nothing goes live without being checked.

There are nine automated tests. They cover creating products, validation, duplicate SKUs, search, updates, deletes, the stats, and the metrics. They run against an in-memory database, so they're fast and never touch real data.

Then a scanner called Trivy checks both container images for known security vulnerabilities. If it finds anything high or critical that already has a fix, the pipeline stops right there. Nine out of nine tests pass, and the scan finds zero serious problems.

## 7. Packed once, runs anywhere
**On screen:** Slide 6, then docker compose up in the terminal

Step two is packing. With Docker, the website, the API and the database each live in their own container. Think of a lunchbox with everything already inside. There's nothing to install and nothing to forget.

One command, docker compose up, and the whole app is running on any computer. Both images also run as a non-root user. It's a small detail, but it makes a big difference for security.

## 8. Every version is saved
**On screen:** Slide 7, then the GitHub container registry

Every image the pipeline builds is pushed to GitHub's container registry, tagged with the exact commit it came from. So if someone asks what's running right now, I can point to the exact line of code. And if a release breaks something, rolling back is just a matter of picking an older tag.

## 9. Servers from a recipe
**On screen:** Slide 8, then terraform plan, the AWS VPC, the EKS nodes, and terraform destroy

Step three is the servers. Instead of clicking around the AWS console, I wrote the infrastructure as code with Terraform. Think of it as a recipe. It describes a private network across two availability zones and a managed Kubernetes cluster, EKS, in the Mumbai region.

Terraform plan shows exactly what's going to be created. I run apply, and about twelve minutes later forty-nine resources are up. Here's the network, and here are the worker nodes, ready to go.

Then, because the cloud bills by the hour, I ran the same recipe in reverse. One terraform destroy and it was all gone. The total cost was under twenty cents.

## 10. Stays up, even when it's busy
**On screen:** Slide 9, then kubectl and helm, then the autoscaler idle and scaled

Inside Kubernetes, everything gets installed with a single Helm chart: the frontend, the backend, Postgres with its own storage, an ingress to route the traffic, and health checks on the app pods.

Two copies of the app are always running, so if one goes down the other carries on.

Then I wanted to see what a busy day looks like, so I pointed a load generator at the API. The CPU shot past the sixty percent target, and the autoscaler started adding pods on its own: three, four, five. When the load stopped, it quietly scaled back down to two.

## 11. A live dashboard
**On screen:** Slide 10, then Prometheus targets, then the Grafana dashboard

But how do I know any of this is actually happening? The backend exposes a metrics endpoint, and Prometheus scrapes it. Here are both backend pods, up and healthy.

Grafana turns those numbers into a live dashboard. It shows requests per second, response time, errors, and how many pods are running. You can actually see the load test here. Traffic spikes, response time stays low, there are zero errors, and the pod count climbs to five.

## 12. Closing the loop
**On screen:** The green GitHub Actions run, then the deploy log

Let's close the loop. This is a real pipeline run on GitHub Actions: test, build and deploy, all green.

The deploy job spins up a fresh Kubernetes cluster right on the runner. It installs the chart with the brand new images and waits for every pod to be ready. Then it calls the API through the frontend. If that last request doesn't come back with real data from Postgres, the run fails. So green really does mean it works.

## 13. What I learned
**On screen:** Slide 11

So what did I learn?

One: let machines do the routine. A pipeline never forgets a step, even on a Friday evening.

Two: keep every version. When you know exactly what's live, problems are quick to fix.

And three: switch off what you don't use. The cloud is like a taxi meter. Build it, use it, remove it.

## 14. Thank you
**On screen:** Slide 12

That's ShopAdmin: a small app with a big safety net around it. Thanks for watching. The code is on GitHub, at THE-ASHUTOSH, slash, shopadmin-capstone.
